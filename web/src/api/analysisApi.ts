import { api } from './index';

export interface StockCandidate {
  code: string;
  name: string;
  market: string;
}

export const analysisApi = {
  analyze: async (code: string): Promise<any> => {
    const result = await api.analyzeStock(code);
    return result;
  },

  analyzeWithLLM: async (code: string): Promise<any> => {
    const result = await api.analyzeWithLLM(code);
    return result;
  },

  marketReview: async (): Promise<any> => {
    const result = await api.marketReview();
    return result;
  },

  searchSuggest: async (q: string, market: string = 'cn'): Promise<StockCandidate[]> => {
    const params = new URLSearchParams({ q, market, limit: '8' });
    const res = await fetch('/api/v1/search/suggest?' + params.toString());
    const data = await res.json();
    return data?.data || [];
  },

  searchRecommend: async (market: string = 'cn', limit: number = 6): Promise<StockCandidate[]> => {
    const params = new URLSearchParams({ market, limit: String(limit) });
    const res = await fetch('/api/v1/search/recommend?' + params.toString());
    const data = await res.json();
    return data?.data || [];
  },
};
