/**
 * ai-bangladesh-address-parser
 * Production-grade AI-powered Bangladeshi address parser
 * 
 * Extracts: house, road, area, district, division, postal code, flat, floor, block
 */

import { PythonShell } from 'python-shell';
import * as path from 'path';
import * as fs from 'fs';

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
}

export interface ExtractionOptions {
  detailed?: boolean;
  timeout?: number; // milliseconds
}

/**
 * Bangladesh Address Extractor
 * 
 * @example
 * ```typescript
 * import { AddressExtractor } from 'ai-bangladesh-address-parser';
 * 
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

  constructor(options?: { pythonPath?: string; scriptPath?: string }) {
    // Find Python script
    const scriptPath = options?.scriptPath || path.join(__dirname, '../python/api.py');
    this.pythonScriptPath = path.resolve(scriptPath);

    // Find Python executable
    this.pythonPath = options?.pythonPath || 'python3';

    // Verify Python script exists
    if (!fs.existsSync(this.pythonScriptPath)) {
      console.warn(`Warning: Python script not found at ${this.pythonScriptPath}`);
      console.warn('Make sure the python/api.py file exists');
    }
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
      const pythonScript = path.join(__dirname, '../python/extract.py');
      
      const pythonOptions = {
        mode: 'text' as const,  // Use 'text' mode to handle JSON manually
        pythonPath: this.pythonPath,
        pythonOptions: ['-u'],
        scriptPath: path.dirname(pythonScript),
        args: [address, options.detailed ? '--detailed' : ''],
      };

      // python-shell v5+ uses Promises, not callbacks
      const timeout = options.timeout || 30000; // 30 seconds default
      
      const extractionPromise = PythonShell.run(
        path.basename(pythonScript),
        pythonOptions
      ).then((results: any[]) => {
        if (!results || results.length === 0) {
          throw new Error('No results returned from Python script');
        }

        // Join all results (in case of multi-line output)
        const output = results.join('').trim();
        
        // Find JSON in output (in case there's any text before/after)
        const jsonMatch = output.match(/\{[\s\S]*\}/);
        if (!jsonMatch) {
          throw new Error('No JSON found in Python output');
        }
        
        try {
          const result = JSON.parse(jsonMatch[0]);
          return result as ExtractionResult;
        } catch (parseError) {
          throw new Error(`Failed to parse Python result: ${parseError}`);
        }
      }).catch((error: any) => {
        throw new Error(`Python extraction error: ${error.message || String(error)}`);
      });

      // Add timeout
      return Promise.race([
        extractionPromise,
        new Promise<ExtractionResult>((_, reject) => {
          setTimeout(() => {
            reject(new Error(`Address extraction timed out after ${timeout}ms`));
          }, timeout);
        })
      ]);
    } catch (error) {
      throw new Error(`Address extraction failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Extract components from multiple addresses (batch processing)
   * 
   * @param addresses - Array of address strings
   * @param options - Extraction options
   * @returns Promise with array of extraction results
   * 
   * @example
   * ```typescript
   * const addresses = [
   *   'House 12, Road 5, Mirpur, Dhaka',
   *   'Banani, Dhaka',
   *   'Gulshan 2, Dhaka'
   * ];
   * const results = await extractor.batchExtract(addresses);
   * results.forEach((result, i) => {
   *   console.log(`${addresses[i]}: ${result.components.postal_code}`);
   * });
   * ```
   */
  async batchExtract(addresses: string[], options: ExtractionOptions = {}): Promise<ExtractionResult[]> {
    const results: ExtractionResult[] = [];

    for (const address of addresses) {
      try {
        const result = await this.extract(address, options);
        results.push(result);
      } catch (error) {
        // Return empty result on error
        results.push(this.emptyResult(address));
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
