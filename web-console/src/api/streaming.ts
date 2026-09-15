import { platformApiUrl } from './client';

export type RuntimeStreamHandler<T> = (event: T) => void;

export const runtimeStream = {
  connect(executionId: string, handler: RuntimeStreamHandler<unknown>) {
    const source = new EventSource(platformApiUrl(`/api/v1/runtime/${executionId}/stream`));

    source.onmessage = (event) => {
      handler(JSON.parse(event.data));
    };

    return {
      close() {
        source.close();
      },
    };
  },
};
