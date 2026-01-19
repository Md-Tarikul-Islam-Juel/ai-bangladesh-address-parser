#!/usr/bin/env node
/**
 * Post-install script for ai-bangladesh-address-parser
 * Automatically installs ALL Python dependencies including spaCy models
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const REQUIREMENTS_FILE = path.join(__dirname, '..', 'requirements.txt');

function findPython() {
  const pythonCommands = ['python3', 'python', 'py'];
  
  for (const cmd of pythonCommands) {
    try {
      const version = execSync(`${cmd} --version`, { encoding: 'utf8', stdio: 'pipe' });
      const match = version.match(/(\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1]);
        const minor = parseInt(match[2]);
        if (major >= 3 && minor >= 9) {
          return cmd;
        }
      }
    } catch (e) {
      // Try next command
      continue;
    }
  }
  return null;
}

function installDependencies(pythonCmd) {
  try {
    console.log('📦 Installing Python dependencies...');
    
    // Check if requirements.txt exists
    if (!fs.existsSync(REQUIREMENTS_FILE)) {
      console.warn('⚠️  requirements.txt not found, skipping Python dependency installation');
      return false;
    }

    // Upgrade pip first to ensure latest version (silently)
    try {
      execSync(
        `${pythonCmd} -m pip install --upgrade pip --quiet --disable-pip-version-check`,
        { stdio: 'ignore', timeout: 30000 }
      );
    } catch (e) {
      // Ignore pip upgrade errors - continue anyway
    }

    // Install all dependencies from requirements.txt
    // Use --user flag as fallback if permission issues
    try {
      execSync(
        `${pythonCmd} -m pip install -r "${REQUIREMENTS_FILE}" --quiet --disable-pip-version-check`,
        { 
          stdio: 'inherit',
          cwd: path.dirname(REQUIREMENTS_FILE),
          timeout: 300000 // 5 minute timeout for large packages like spacy
        }
      );
    } catch (error) {
      // Try with --user flag if permission denied
      if (error.message.includes('permission') || error.message.includes('Permission')) {
        console.log('   Retrying with user installation...');
        execSync(
          `${pythonCmd} -m pip install -r "${REQUIREMENTS_FILE}" --user --quiet --disable-pip-version-check`,
          { 
            stdio: 'inherit',
            cwd: path.dirname(REQUIREMENTS_FILE),
            timeout: 300000
          }
        );
      } else {
        throw error;
      }
    }
    
    console.log('✅ Python dependencies installed successfully');
    return true;
  } catch (error) {
    console.warn('⚠️  Could not automatically install Python dependencies');
    console.warn('   Please install manually: pip install -r requirements.txt');
    console.warn(`   Error: ${error.message}`);
    return false;
  }
}

function downloadSpacyModel(pythonCmd) {
  try {
    console.log('📥 Checking spaCy models...');
    
    // Check if spaCy is installed first
    try {
      execSync(
        `${pythonCmd} -c "import spacy"`,
        { stdio: 'ignore' }
      );
    } catch (e) {
      console.log('ℹ️  spaCy not available, skipping model download');
      return true;
    }
    
    // Try to download a base English model as fallback
    // The custom trained model will be used if available
    try {
      execSync(
        `${pythonCmd} -m spacy download en_core_web_sm --quiet`,
        { stdio: 'pipe', timeout: 60000 } // 60 second timeout
      );
      console.log('✅ spaCy base model available');
    } catch (error) {
      // Model might already be installed or download failed
      // This is not critical - custom model will be used if available
      console.log('ℹ️  Using custom trained model (if available)');
    }
    
    return true;
  } catch (error) {
    // Not critical - code will work without base model
    console.log('ℹ️  spaCy model check completed');
    return true;
  }
}

function verifyInstallation(pythonCmd) {
  try {
    console.log('🔍 Verifying installation...');
    
    // Check if key packages are importable
    const checkScript = `
import sys
errors = []
try:
    import spacy
except ImportError as e:
    errors.append(f"spacy: {e}")
try:
    import pygtrie
except ImportError as e:
    errors.append(f"pygtrie: {e}")

if errors:
    print("\\n".join(errors), file=sys.stderr)
    sys.exit(1)
else:
    print("✅ All Python dependencies verified")
`;
    
    execSync(
      `${pythonCmd} -c "${checkScript}"`,
      { encoding: 'utf8', stdio: 'pipe' }
    );
    
    return true;
  } catch (error) {
    console.warn('⚠️  Some Python packages may not be installed correctly');
    return false;
  }
}

// Main execution
function main() {
  console.log('🚀 Setting up ai-bangladesh-address-parser...\n');
  
  const pythonCmd = findPython();
  
  if (!pythonCmd) {
    console.warn('⚠️  Python 3.9+ not found');
    console.warn('   Please install Python 3.9+ from https://www.python.org/downloads/');
    console.warn('   Then run: npm install ai-bangladesh-address-parser again');
    process.exit(0); // Don't fail npm install, just warn
    return;
  }

  console.log(`🐍 Found Python: ${pythonCmd}\n`);
  
  // Step 1: Install all Python dependencies
  const depsInstalled = installDependencies(pythonCmd);
  
  if (depsInstalled) {
    // Step 2: Download spaCy model if needed (non-blocking)
    downloadSpacyModel(pythonCmd);
    
    // Step 3: Verify installation
    const verified = verifyInstallation(pythonCmd);
    
    if (verified) {
      console.log('\n✨ Installation complete! Ready to use.');
      console.log('   You can now use: const extractor = new AddressExtractor();\n');
    } else {
      console.log('\n⚠️  Installation completed with warnings.');
      console.log('   The package may still work, but some features might be limited.\n');
    }
  } else {
    console.warn('\n⚠️  Python dependencies installation failed');
    console.warn('   Please install manually:');
    console.warn(`   ${pythonCmd} -m pip install -r requirements.txt\n`);
  }
}

// Run only if this is a direct install (not in node_modules)
if (require.main === module) {
  main();
}

module.exports = { findPython, installDependencies, downloadSpacyModel, verifyInstallation };
