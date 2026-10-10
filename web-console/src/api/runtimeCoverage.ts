export interface RuntimeCoverage {
  loaded: number;
  total: number | null;
  incomplete: boolean;
  warning: string | null;
}

/** 仅描述返回页覆盖范围，不把首 100 条误写为全量生产状态。 */
export function summarizeRuntimeCoverage(
  loaded: number, total: number | null, hasMore: boolean, errors: string[] = []
): RuntimeCoverage {
  const count = Number.isSafeInteger(loaded) && loaded >= 0 ? loaded : 0;
  const finite = total != null && Number.isSafeInteger(total) && total >= 0 ? total : null;
  const incomplete = Boolean(hasMore || (finite !== null && count < finite));
  const issues = errors.length ? '接口返回部分错误；' : '';
  return {
    loaded: count,
    total: finite,
    incomplete,
    warning: issues + (incomplete ? '目前仅展示部分阶段摘要，完整分页请前往工作流。' : '') || null,
  };
}
