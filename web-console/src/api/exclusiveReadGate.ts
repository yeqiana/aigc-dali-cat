/** 只读查询代际锁，防止重叠请求和卸载后的旧结果回写。 */
export class ExclusiveReadGate {
  private generation = 0;
  private inFlight = false;
  begin(): number | null {
    if (this.inFlight) return null;
    this.inFlight = true;
    return ++this.generation;
  }
  isCurrent(generation: number): boolean {
    return this.inFlight && this.generation === generation;
  }
  finish(generation: number): boolean {
    if (!this.isCurrent(generation)) return false;
    this.inFlight = false;
    return true;
  }
  invalidate(): void {
    ++this.generation;
    this.inFlight = false;
  }
}
