import React, { useState } from 'react';
import {
  UserCheck,
  Lock,
  Unlock,
  ShieldAlert,
  Sun,
  Shirt,
  Sparkles,
  CheckCircle2
} from 'lucide-react';
import { CharacterContract } from '../types';

interface CharacterContractCardProps {
  characters: CharacterContract[];
}

export const CharacterContractCard: React.FC<CharacterContractCardProps> = ({ characters }) => {
  const [characterList, setCharacterList] = useState<CharacterContract[]>(characters);

  const toggleLock = (charId: string) => {
    setCharacterList(prev => prev.map(c => {
      if (c.id === charId) {
        return {
          ...c,
          status: c.status === 'locked' ? 'calibrating' : 'locked',
        };
      }
      return c;
    }));
  };

  return (
    <div id="character-contract-card" className="bg-white rounded-xl border border-zinc-200 p-4 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-zinc-900 text-amber-400">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wide">
                人物合同与面容锁 (Character Consistency Contracts)
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-700 font-semibold border border-zinc-300">
                模拟演示数据 · 角色特征
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold">
                {characterList.filter(c => c.status === 'locked').length}/{characterList.length} LOCKED
              </span>
            </div>
            <p className="text-[11px] text-zinc-600 mt-0.5">固定特征面容语义、指定穿戴规约与绝对负向禁则</p>
          </div>
        </div>

        <span className="text-[11px] font-mono text-zinc-600">
          余弦相似度门限: &gt; 96.5%
        </span>
      </div>

      {/* Characters List Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {characterList.map((char) => {
          const isLocked = char.status === 'locked';

          return (
            <div
              key={char.id}
              className={`p-3 rounded-lg border transition-all flex flex-col justify-between ${
                isLocked
                  ? 'bg-zinc-50/70 border-zinc-200'
                  : 'bg-amber-50/40 border-amber-300 ring-1 ring-amber-300/40'
              }`}
            >
              <div>
                {/* Character Top Info */}
                <div className="flex items-start gap-2.5 mb-2.5">
                  <img
                    src={char.avatar}
                    alt={char.name}
                    className="w-12 h-12 rounded-md object-cover border border-zinc-300 shrink-0"
                    referrerPolicy="no-referrer"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-zinc-900 truncate">{char.name}</h4>
                      <button
                        onClick={() => toggleLock(char.id)}
                        className={`p-1 rounded text-xs transition-colors ${
                          isLocked
                            ? 'text-emerald-600 hover:bg-emerald-50'
                            : 'text-amber-600 hover:bg-amber-100'
                        }`}
                        title={isLocked ? '点击解锁面部权重' : '点击锁定面部'}
                      >
                        {isLocked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <p className="text-[11px] text-zinc-600 truncate">{char.role}</p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="text-[10px] font-mono bg-zinc-200/80 text-zinc-700 px-1 py-0.2 rounded truncate max-w-[110px]">
                        {char.faceEmbeddingId}
                      </span>
                      <span className="text-[10px] font-mono font-bold text-emerald-700">
                        {char.consistencyScore}% 一致
                      </span>
                    </div>
                  </div>
                </div>

                {/* Fixed Costume & Lighting */}
                <div className="space-y-1.5 text-[11px] border-t border-zinc-200/60 pt-2 mb-2">
                  <div className="flex items-start gap-1.5 text-zinc-700">
                    <Shirt className="w-3.5 h-3.5 text-zinc-400 shrink-0 mt-0.5" />
                    <span className="leading-tight">{char.fixedCostume}</span>
                  </div>
                  <div className="flex items-start gap-1.5 text-zinc-700">
                    <Sun className="w-3.5 h-3.5 text-zinc-400 shrink-0 mt-0.5" />
                    <span className="leading-tight text-zinc-600">{char.lightingAnchor}</span>
                  </div>
                </div>
              </div>

              {/* Negative constraints (Banned Traits) */}
              <div className="pt-2 border-t border-zinc-200/60">
                <div className="flex items-center gap-1 text-[10px] font-mono text-rose-600 font-bold mb-1">
                  <ShieldAlert className="w-3 h-3" />
                  <span>负向约束规约：</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {char.negativeConstraints.map((neg, i) => (
                    <span
                      key={i}
                      className="text-[10px] px-1.5 py-0.2 rounded bg-rose-50 text-rose-700 border border-rose-200/70 font-mono"
                    >
                      {neg}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
