import React, {useEffect,useState} from 'react';
import {ConfigProvider,theme as antdTheme} from 'antd';
import {THEME_PALETTES} from '../theme';
const readMode=()=>(document.documentElement.classList.contains('theme-light-gradient')?'light-gradient':document.documentElement.classList.contains('theme-light')?'light':'dark') as keyof typeof THEME_PALETTES;
const AntdSurface:React.FC<{children:React.ReactNode}>=({children})=>{
 const [mode,setMode]=useState<keyof typeof THEME_PALETTES>(()=>typeof document==='undefined'?'dark':readMode());
 useEffect(()=>{const observer=new MutationObserver(()=>setMode(readMode()));observer.observe(document.documentElement,{attributes:true,attributeFilter:['class']});return ()=>observer.disconnect()},[]);
 const c=THEME_PALETTES[mode];
 return <ConfigProvider componentSize="small" theme={{algorithm:mode==='dark'?antdTheme.darkAlgorithm:antdTheme.defaultAlgorithm,token:{colorPrimary:c.info,colorBgContainer:c.bgSurface,colorText:c.textPrimary,colorTextSecondary:c.textSecondary,colorBorder:c.borderNormal,colorBorderSecondary:c.borderSubtle,borderRadius:6,fontSize:13,controlHeight:32},components:{Table:{cellPaddingBlockSM:8,cellPaddingInlineSM:12}}}}>{children}</ConfigProvider>;
};
export default AntdSurface;
