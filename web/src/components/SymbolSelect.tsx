import { useState, useEffect } from 'react';
import { AutoComplete } from 'antd';
import { api } from '../api';

interface Props {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  style?: React.CSSProperties;
}

/** 股票代码输入框：可自由输入，也可下拉选择「自选 + 持仓」去重后的代码（页面打开时加载） */
export default function SymbolSelect({ value, onChange, placeholder, style }: Props) {
  const [symbols, setSymbols] = useState<any[]>([]);

  useEffect(() => {
    api.getSymbols().then(d => setSymbols(d.data || [])).catch(() => {});
  }, []);

  const options = symbols.map(s => ({
    value: s.code,
    label: s.name ? `${s.code}  ${s.name}` : s.code,
  }));

  return (
    <AutoComplete
      value={value}
      options={options}
      onChange={onChange}
      placeholder={placeholder || '股票代码（可下拉选择自选/持仓）'}
      style={style || { width: '100%' }}
      listHeight={320}  /* 约 10 项，超过滚动 */
      filterOption={(input, option) =>
        String(option?.value).toUpperCase().includes(input.toUpperCase()) ||
        String(option?.label).toUpperCase().includes(input.toUpperCase())
      }
    />
  );
}
