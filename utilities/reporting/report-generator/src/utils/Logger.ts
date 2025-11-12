import winston from 'winston';

/**
 * Structured logging service following Semgrep coding standards
 * 
 * Usage Guidelines:
 * - Use logging module for operational logging
 * - Reserve console output for CLI user-facing messages
 * - Include context and structured data in log messages
 */

// Configure Winston logger with structured format
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json(),
    winston.format.colorize({ all: true })
  ),
  defaultMeta: { service: 'semgrep-reporter' },
  transports: [
    // Write to file for operational logs
    new winston.transports.File({ 
      filename: 'logs/error.log', 
      level: 'error',
      format: winston.format.json()
    }),
    new winston.transports.File({ 
      filename: 'logs/combined.log',
      format: winston.format.json()
    }),
  ],
});

// Add console transport for development (structured logs, not user output)
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

/**
 * Structured logging interface following Semgrep standards
 */
export class Logger {
  
  static info(message: string, context?: any): void {
    logger.info(message, context);
  }
  
  static warn(message: string, context?: any): void {
    logger.warn(message, context);
  }
  
  static error(message: string, error?: Error, context?: any): void {
    logger.error(message, { error: error?.message, stack: error?.stack, ...context });
  }
  
  static debug(message: string, context?: any): void {
    logger.debug(message, context);
  }
  
  /**
   * Log API operations with structured context
   */
  static apiCall(operation: string, context: { endpoint?: string, status?: number, duration?: number, organization?: string }): void {
    logger.info(`API Operation: ${operation}`, {
      type: 'api_call',
      operation,
      ...context
    });
  }
  
  /**
   * Log security-related events
   */
  static security(event: string, context?: any): void {
    logger.warn(`Security Event: ${event}`, {
      type: 'security',
      event,
      ...context
    });
  }
  
  /**
   * Log application performance metrics
   */
  static performance(metric: string, value: number, unit: string, context?: any): void {
    logger.info(`Performance Metric: ${metric}`, {
      type: 'performance',
      metric,
      value,
      unit,
      ...context
    });
  }
}

/**
 * CLI output utilities for user-facing messages
 * Use these instead of console.log for user communication
 */
export class CLIOutput {
  
  static info(message: string): void {
    console.log(`ℹ️  ${message}`);
  }
  
  static success(message: string): void {
    console.log(`✅ ${message}`);
  }
  
  static warning(message: string): void {
    console.log(`⚠️  ${message}`);
  }
  
  static error(message: string): void {
    console.error(`❌ ${message}`);
  }
  
  static progress(message: string): void {
    console.log(`🔄 ${message}`);
  }
  
  static result(message: string): void {
    console.log(`📊 ${message}`);
  }
  
  static section(title: string): void {
    console.log(`\n📋 ${title}`);
    console.log('='.repeat(50));
  }
}

export default Logger;