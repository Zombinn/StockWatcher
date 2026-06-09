import { useState, useCallback } from 'react';
import { api } from '../api';

/** 自选股状态 + 刷新，供各页面复用，避免重复的 try/catch 模板代码 */
export function useWatchlist() {
  const [watchlistCodes, setWatchlistCodes] = useState<Set<string>>(new Set());

  const loadWatchlist = useCallback(async () => {
    try {
      const r = await api.getWatchlist();
      setWatchlistCodes(new Set((r.data || []).map((s: any) => s.code as string)));
    } catch {}
  }, []);

  return { watchlistCodes, loadWatchlist };
}
