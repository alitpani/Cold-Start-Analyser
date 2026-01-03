import { Module } from 'module';
// @ts-ignore
const originalRequire = Module.prototype.require;
const moduleTimings: Record<string, number> = {};

// Hook into require to capture timings
// @ts-ignore
Module.prototype.require = function (id: string) {
    const start = process.hrtime.bigint();
    const result = originalRequire.call(this, id);
    const end = process.hrtime.bigint();

    const durationMs = Number(end - start) / 1e6;
    if (durationMs > 1) {
        moduleTimings[id] = (moduleTimings[id] || 0) + durationMs;
    }
    return result;
};

export interface AnalyzerConfig {
    apiKey?: string;
    endpoint?: string;
    enabled?: boolean;
}

export function analyze(handler: Function, config: AnalyzerConfig = {}) {
    let isFirstInvocation = true;

    return async (event: any, context: any) => {
        let coldStart = false;
        if (isFirstInvocation) {
            coldStart = true;
            isFirstInvocation = false;
        }

        const start = Date.now();
        try {
            const result = await handler(event, context);
            // In a real app, we would send telemetry here
            console.log('ColdStart Analysis:', {
                coldStart,
                executionTime: Date.now() - start,
                moduleTimings: coldStart ? moduleTimings : {}
            });
            return result;
        } catch (error) {
            throw error;
        }
    };
}
