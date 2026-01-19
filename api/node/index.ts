/**
 * ai-bangladesh-address-parser
 * Production-grade AI-powered Bangladeshi address parser
 * 
 * Extracts: house, road, area, district, division, postal code, flat, floor, block
 */

import { PythonShell } from 'python-shell';
import * as path from 'path';
import * as fs from 'fs';
import { execSync } from 'child_process';

export interface ExtractedAddress {
  house_number?: string;
  road?: string;
  area?: string;
  district?: string;
  division?: string;
  postal_code?: string;
  flat_number?: string;
  floor_number?: string;
  block_number?: string;
}

export interface ExtractionResult {
  components: ExtractedAddress;
  overall_confidence: number;
  extraction_time_ms: number;
  normalized_address: string;
  original_address: string;
  cached?: boolean;
  metadata?: {
    script?: string;
    is_mixed?: boolean;
    conflicts?: string[];
    component_details?: Record<string, {
      value: string;
      confidence: number;
      source: string;
    }>;
    enabled_stages?: string[];
  };
}

export interface ExtractionOptions {
  detailed?: boolean;
  timeout?: number; // milliseconds
}

export interface ConfidenceThresholds {
  house_number?: number;
  road?: number;
  area?: number;
  district?: number;
  division?: number;
  postal_code?: number;
  flat_number?: number;
  floor_number?: number;
  block_number?: number;
}

/**
 * Bangladesh Address Extractor
 * 
 * Python is automatically detected and managed - no configuration needed!
 * The package will find Python (python3, python, or py) automatically.
 * 
 * @example
 * ```typescript
 * import { AddressExtractor } from 'ai-bangladesh-address-parser';
 * 
 * // Python is automatically detected - zero configuration!
 * const extractor = new AddressExtractor();
 * const result = await extractor.extract('House 12, Road 5, Mirpur, Dhaka-1216');
 * console.log(result.components);
 * // { house_number: '12', road: '5', area: 'Mirpur', district: 'Dhaka', postal_code: '1216' }
 * ```
 */
export class AddressExtractor {
  private pythonScriptPath: string;
  private pythonPath: string;
  private initialized: boolean = false;
  private confidenceThresholds: ConfidenceThresholds | null = null;

  /**
   * Creates a new AddressExtractor instance.
   * 
   * Python is automatically detected and managed internally.
   * No configuration needed - just create and use!
   */
  constructor() {
    // Find Python script automatically
    // In npm package: __dirname points to dist/, so go up to package root
    this.pythonScriptPath = path.resolve(path.join(__dirname, '../api/python/extract.py'));

    // Python is managed completely internally - automatically detected
    // Tries python3, python, then py and verifies Python 3.9+
    const detected = this.findPython();
    if (detected) {
      this.pythonPath = detected;
    } else {
      // Fallback to python3 (most common)
      this.pythonPath = 'python3';
    }

    // Verify Python script exists
    if (!fs.existsSync(this.pythonScriptPath)) {
      console.warn(`Warning: Python script not found at ${this.pythonScriptPath}`);
      console.warn('Make sure the api/python/extract.py file exists');
    }
  }

  /**
   * Auto-detect Python executable
   */
  private findPython(): string | null {
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

  /**
   * Set confidence thresholds for address components
   * 
   * Components with confidence below the threshold will be filtered out from results.
   * 
   * @param thresholds - Dictionary with minimum confidence thresholds (0.0-1.0) for each component
   * @returns void
   * 
   * @example
   * ```typescript
   * extractor.setConfidenceThresholds({
   *   house_number: 0.75,
   *   postal_code: 0.85,
   *   area: 0.70
   * });
   * ```
   */
  setConfidenceThresholds(thresholds: ConfidenceThresholds): void {
    // Validate thresholds are between 0 and 1
    for (const [key, value] of Object.entries(thresholds)) {
      if (value !== undefined && (value < 0 || value > 1)) {
        throw new Error(`Invalid threshold for ${key}: ${value}. Must be between 0.0 and 1.0`);
      }
    }
    this.confidenceThresholds = thresholds;
  }

  /**
   * Get current confidence thresholds
   * 
   * @returns Current confidence thresholds or null if not set
   */
  getConfidenceThresholds(): ConfidenceThresholds | null {
    return this.confidenceThresholds;
  }

  /**
   * Extract address components from a full address string
   * 
   * @param address - Full address string (e.g., "House 12, Road 5, Mirpur, Dhaka-1216")
   * @param options - Extraction options
   * @returns Promise with extracted components and metadata
   * 
   * @example
   * ```typescript
   * const result = await extractor.extract('Flat A-3, Building 7, Bashundhara R/A, Dhaka');
   * console.log(result.components.area); // "Bashundhara R/A"
   * console.log(result.overall_confidence); // 0.95
   * ```
   */
  async extract(address: string, options: ExtractionOptions = {}): Promise<ExtractionResult> {
    if (!address || typeof address !== 'string' || !address.trim()) {
      return this.emptyResult(address || '');
    }

    try {
      const pythonScript = path.join(__dirname, '../api/python/extract.py');
      const args: string[] = ['extract', address];
      
      if (options.detailed) {
        args.push('--detailed');
      }
      
      if (this.confidenceThresholds) {
        args.push('--thresholds', JSON.stringify(this.confidenceThresholds));
      }

      const timeout = options.timeout || 30000;
      const result = await this._runPythonScript(pythonScript, args, timeout);
      return result as ExtractionResult;
    } catch (error) {
      throw new Error(`Address extraction failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Extract components from multiple addresses (batch processing)
   * 
   * @param addresses - Array of address strings
   * @param options - Extraction options with optional progress/error callbacks
   * @returns Promise with array of extraction results
   * 
   * @example
   * ```typescript
   * const addresses = [
   *   'House 12, Road 5, Mirpur, Dhaka',
   *   'Banani, Dhaka',
   *   'Gulshan 2, Dhaka'
   * ];
   * 
   * const results = await extractor.batchExtract(addresses, {
   *   onProgress: (current, total) => {
   *     console.log(`Processing ${current}/${total}`);
   *   },
   *   onError: (address, error) => {
   *     console.error(`Failed: ${address}`, error);
   *   }
   * });
   * 
   * results.forEach((result, i) => {
   *   console.log(`${addresses[i]}: ${result.components.postal_code}`);
   * });
   * ```
   */
  async batchExtract(
    addresses: string[], 
    options: ExtractionOptions & {
      onProgress?: (current: number, total: number) => void;
      onError?: (address: string, error: Error) => void;
    } = {}
  ): Promise<ExtractionResult[]> {
    const results: ExtractionResult[] = [];
    const total = addresses.length;

    for (let i = 0; i < addresses.length; i++) {
      const address = addresses[i];
      try {
        const result = await this.extract(address, options);
        results.push(result);
        
        if (options.onProgress) {
          options.onProgress(i + 1, total);
        }
      } catch (error) {
        // Return empty result on error
        results.push(this.emptyResult(address));
        
        if (options.onError) {
          options.onError(address, error instanceof Error ? error : new Error(String(error)));
        }
      }
    }

    return results;
  }

  /**
   * Check if the Python extraction system is available
   * 
   * @returns Promise<boolean> - True if Python system is ready
   */
  async isAvailable(): Promise<boolean> {
    try {
      const testResult = await this.extract('test', { timeout: 5000 });
      return testResult !== null;
    } catch {
      return false;
    }
  }

  /**
   * Get version information
   */
  getVersion(): string {
    const packageJson = require('../package.json');
    return packageJson.version;
  }

  /**
   * Validate address completeness and component validity
   * 
   * @param address - Address string to validate
   * @param required - Optional list of required components (default: ['district', 'area'])
   * @returns Promise with validation result
   * 
   * @example
   * ```typescript
   * const validation = await extractor.validate("House 12, Road 5, Mirpur, Dhaka-1216");
   * console.log(validation.is_valid); // true
   * console.log(validation.completeness); // 0.89
   * ```
   */
  async validate(address: string, required?: string[]): Promise<any> {
    try {
      const pythonScript = path.join(__dirname, '../api/python/extract.py');
      const args: string[] = ['validate', address];
      
      if (required && required.length > 0) {
        args.push('--required', required.join(','));
      }
      
      if (this.confidenceThresholds) {
        args.push('--thresholds', JSON.stringify(this.confidenceThresholds));
      }

      const result = await this._runPythonScript(pythonScript, args);
      return result;
    } catch (error) {
      throw new Error(`Address validation failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Format address into standardized string
   * 
   * @param address - Address string to format
   * @param options - Formatting options
   * @returns Promise with formatted address string
   * 
   * @example
   * ```typescript
   * const formatted = await extractor.format("House 12, Road 5, Mirpur, Dhaka-1216", {
   *   style: 'short',
   *   separator: ', ',
   *   includePostal: true
   * });
   * // "Mirpur, Dhaka, 1216"
   * ```
   */
  async format(address: string, options: {
    style?: 'full' | 'short' | 'postal' | 'minimal';
    separator?: string;
    includePostal?: boolean;
  } = {}): Promise<string> {
    try {
      const pythonScript = path.join(__dirname, '../api/python/extract.py');
      const args: string[] = ['format', address];
      
      if (options.style) {
        args.push('--style', options.style);
      }
      if (options.separator) {
        args.push('--separator', options.separator);
      }
      if (options.includePostal === false) {
        args.push('--no-postal');
      }
      
      if (this.confidenceThresholds) {
        args.push('--thresholds', JSON.stringify(this.confidenceThresholds));
      }

      const result = await this._runPythonScript(pythonScript, args);
      return result.formatted || '';
    } catch (error) {
      throw new Error(`Address formatting failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Compare two addresses and calculate similarity
   * 
   * @param address1 - First address string
   * @param address2 - Second address string
   * @returns Promise with comparison result
   * 
   * @example
   * ```typescript
   * const comparison = await extractor.compare(
   *   "House 12, Road 5, Mirpur, Dhaka",
   *   "H-12, R-5, Mirpur, Dhaka-1216"
   * );
   * console.log(comparison.similarity); // 0.92
   * console.log(comparison.match); // true
   * ```
   */
  async compare(address1: string, address2: string): Promise<any> {
    try {
      const pythonScript = path.join(__dirname, '../api/python/extract.py');
      const args: string[] = ['compare', address1, address2];
      
      if (this.confidenceThresholds) {
        args.push('--thresholds', JSON.stringify(this.confidenceThresholds));
      }

      const result = await this._runPythonScript(pythonScript, args);
      return result;
    } catch (error) {
      throw new Error(`Address comparison failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Suggest addresses based on query (area/district name)
   * 
   * @param query - Search query (area or district name)
   * @param limit - Maximum number of suggestions (default: 5)
   * @returns Promise with array of suggestions
   * 
   * @example
   * ```typescript
   * const suggestions = await extractor.suggest("Mirpur", { limit: 5 });
   * suggestions.forEach(s => {
   *   console.log(`${s.area}, ${s.district} - ${s.postal_code}`);
   * });
   * ```
   */
  async suggest(query: string, limit: number = 5): Promise<any[]> {
    try {
      const pythonScript = path.join(__dirname, '../api/python/extract.py');
      const args: string[] = ['suggest', query, '--limit', limit.toString()];
      
      if (this.confidenceThresholds) {
        args.push('--thresholds', JSON.stringify(this.confidenceThresholds));
      }

      const result = await this._runPythonScript(pythonScript, args);
      return result.suggestions || [];
    } catch (error) {
      throw new Error(`Address suggestion failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }


  /**
   * Enrich address with additional geographic information
   * 
   * @param address - Address string
   * @returns Promise with enriched address data
   * 
   * @example
   * ```typescript
   * const enriched = await extractor.enrich("Mirpur, Dhaka");
   * console.log(enriched.hierarchy); // Geographic hierarchy
   * console.log(enriched.suggested_postal_code); // Suggested postal code if missing
   * ```
   */
  async enrich(address: string): Promise<any> {
    try {
      const pythonScript = path.join(__dirname, '../api/python/extract.py');
      const args: string[] = ['enrich', address];
      
      if (this.confidenceThresholds) {
        args.push('--thresholds', JSON.stringify(this.confidenceThresholds));
      }

      const result = await this._runPythonScript(pythonScript, args);
      return result;
    } catch (error) {
      throw new Error(`Address enrichment failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Calculate statistics for a list of addresses
   * 
   * @param addresses - Array of address strings
   * @returns Promise with statistics
   * 
   * @example
   * ```typescript
   * const stats = await extractor.getStatistics([
   *   "House 12, Mirpur, Dhaka",
   *   "Banani, Dhaka",
   *   "Gulshan, Dhaka"
   * ]);
   * console.log(stats.completeness); // 0.87
   * console.log(stats.distribution.districts); // { "Dhaka": 3 }
   * ```
   */
  async getStatistics(addresses: string[]): Promise<any> {
    try {
      const pythonScript = path.join(__dirname, '../api/python/extract.py');
      const args: string[] = ['statistics', JSON.stringify(addresses)];
      
      if (this.confidenceThresholds) {
        args.push('--thresholds', JSON.stringify(this.confidenceThresholds));
      }

      const result = await this._runPythonScript(pythonScript, args);
      return result.statistics || {};
    } catch (error) {
      throw new Error(`Statistics calculation failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Internal method to run Python script and parse JSON output
   */
  private async _runPythonScript(scriptPath: string, args: string[], timeout: number = 30000): Promise<any> {
    const pythonOptions = {
      mode: 'text' as const,
      pythonPath: this.pythonPath,
      pythonOptions: ['-u'],
      scriptPath: path.dirname(scriptPath),
      args: args,
    };

    const extractionPromise = PythonShell.run(
      path.basename(scriptPath),
      pythonOptions
    ).then((results: any[]) => {
      if (!results || results.length === 0) {
        throw new Error('No results returned from Python script');
      }

      const output = results.join('').trim();
      const jsonMatch = output.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in Python output');
      }

      try {
        return JSON.parse(jsonMatch[0]);
      } catch (parseError) {
        throw new Error(`Failed to parse Python result: ${parseError}`);
      }
    }).catch((error: any) => {
      throw new Error(`Python execution error: ${error.message || String(error)}`);
    });

    return Promise.race([
      extractionPromise,
      new Promise<any>((_, reject) => {
        setTimeout(() => {
          reject(new Error(`Operation timed out after ${timeout}ms`));
        }, timeout);
      })
    ]);
  }

  private emptyResult(address: string): ExtractionResult {
    return {
      components: {},
      overall_confidence: 0.0,
      extraction_time_ms: 0,
      normalized_address: '',
      original_address: address,
    };
  }
}

// Default export
export default AddressExtractor;
