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
    <div id="character-contract-card" className="storyos-surface p-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide">
                人物合同与面容锁 (Character Consistency Contracts)
              </h3>
              <span className="storyos-status storyos-status--neutral font-mono">
                模拟演示数据 · 角色特征
              </span>
              <span className="storyos-status storyos-status--success font-mono">
                {characterList.filter(c => c.status === 'locked').length}/{characterList.length} LOCKED
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">固定特征面容语义、指定穿戴规约与绝对负向禁则</p>
          </div>
        </div>

        <span className="text-[11px] font-mono text-[var(--text-tertiary)]">
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
              className={`p-3 rounded-[var(--radius-md)] border transition-colors flex flex-col justify-between ${
                isLocked
                  ? 'bg-[var(--bg-subtle)] border-[var(--border-normal)]'
                  : 'bg-[var(--warning-soft)] border-[var(--warning)] ring-1 ring-[var(--warning-soft)]'
              }`}
            >
              <div>
                {/* Character Top Info */}
                <div className="flex items-start gap-2.5 mb-2.5">
                  <img
                    src={char.avatar}
                    alt={char.name}
                    className="w-12 h-12 rounded-[var(--radius-sm)] object-cover border border-[var(--border-normal)] shrink-0"
                    referrerPolicy="no-referrer"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-semibold text-[var(--text-primary)] truncate">{char.name}</h4>
                      <button
                        onClick={() => toggleLock(char.id)}
                        className={`p-1 rounded text-xs transition-colors ${
                          isLocked
                            ? 'text-[var(--success)] hover:bg-[var(--success-soft)]'
                            : 'text-[var(--warning)] hover:bg-[var(--warning-soft)]'
                        }`}
                        title={isLocked ? '点击解锁面部权重' : '点击锁定面部'}
                      >
                        {isLocked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <p className="text-[11px] text-[var(--text-tertiary)] truncate">{char.role}</p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="text-[10px] font-mono bg-[var(--bg-muted)] text-[var(--text-secondary)] px-1 py-0.5 rounded-[var(--radius-xs)] truncate max-w-[110px]">
                        {char.faceEmbeddingId}
                      </span>
                      <span className="text-[10px] font-mono font-semibold text-[var(--success)]">
                        {char.consistencyScore}% 一致
                      </span>
                    </div>
                  </div>
                </div>

                {/* Fixed Costume & Lighting */}
                <div className="space-y-1.5 text-[11px] border-t border-[var(--border-subtle)] pt-2 mb-2">
                  <div className="flex items-start gap-1.5 text-[var(--text-secondary)]">
                    <Shirt className="w-3.5 h-3.5 text-[var(--text-subtle)] shrink-0 mt-0.5" />
                    <span className="leading-tight">{char.fixedCostume}</span>
                  </div>
                  <div className="flex items-start gap-1.5 text-[var(--text-secondary)]">
                    <Sun className="w-3.5 h-3.5 text-[var(--text-subtle)] shrink-0 mt-0.5" />
                    <span className="leading-tight text-[var(--text-tertiary)]">{char.lightingAnchor}</span>
                  </div>
                </div>
              </div>

              {/* Negative constraints (Banned Traits) */}
              <div className="pt-2 border-t border-[var(--border-subtle)]">
                <div className="flex items-center gap-1 text-[10px] font-mono text-[var(--danger)] font-semibold mb-1">
                  <ShieldAlert className="w-3 h-3" />
                  <span>负向约束规约：</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {char.negativeConstraints.map((neg, i) => (
                    <span
                      key={i}
                      className="text-[10px] px-1.5 py-0.5 rounded-[var(--radius-xs)] bg-[var(--danger-soft)] text-[var(--danger)] border border-[var(--danger)] font-mono"
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
