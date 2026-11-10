#!/usr/bin/env python3
"""Publication figure from author-supplied marginal rating counts."""
from pathlib import Path
import csv
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent
with (ROOT / 'technician_rating_counts.csv').open() as f:
    rows = list(csv.reader(f))[1:]
counts = np.array([[int(x) for x in row[1:]] for row in rows])
assert counts.shape == (3, 5) and (counts >= 0).all() and (counts.sum(1) == 80).all()
colors = ['#B97850', '#E1BD96', '#C7CDD2', '#80ACC2', '#285C79']
plt.rcParams.update({'font.family':'serif', 'font.serif':['Times New Roman','DejaVu Serif'],
    'font.size':12, 'pdf.fonttype':42, 'ps.fonttype':42, 'savefig.dpi':400})
# Leave room for larger labels at the manuscript's existing display width.
fig = plt.figure(figsize=(7.2, 2.35), facecolor='white')
ax = fig.add_axes([.18,.29,.61,.40])
y = np.arange(3)
left = np.zeros(3)
for j, color in enumerate(colors):
    values = counts[:,j]/80*100
    ax.barh(y, values, left=left, height=.62, color=color,
            edgecolor='white', linewidth=.6, zorder=3)
    left += values
ax.set_ylim(2.39,-.39)
ax.set_xlim(0,100)
ax.set_yticks(y, ['Technician '+r[0] for r in rows], color='#283A47')
ax.tick_params(axis='y', length=0, pad=8, labelsize=12)
ax.set_xticks([0,25,50,75,100], ['0','25','50','75','100'])
ax.tick_params(axis='x', length=3, width=.6, pad=5, labelsize=11, colors='#455563')
ax.grid(axis='x', color='#E8EDF0', linewidth=.6, zorder=0)
for spine in ax.spines.values(): spine.set_visible(False)
ax.spines['bottom'].set_visible(True)
ax.spines['bottom'].set_color('#A5AFB8')
ax.spines['bottom'].set_linewidth(.65)
ax.set_xlabel('Share of ratings (%)', fontsize=12, color='#455563', labelpad=4)
for i in range(3):
    ax.text(1.18, i, f"{(Decimal(int(counts[i,3:].sum())) * 100 / 80).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%",
        transform=ax.get_yaxis_transform(), ha='center', va='center',
        fontsize=12, fontweight='medium', color='#193E56', clip_on=False)
fig.text(.90,.75,'No or minor\nmodification',fontsize=10,ha='center',linespacing=1.1,color='#455563')
labels=['1  Unusable','2  Major','3  Moderate','4  Minor','5  None']
fig.legend([Patch(facecolor=c,edgecolor='none') for c in colors],labels,
    loc='upper center',bbox_to_anchor=(.50,.99),ncol=5,frameon=False,
    fontsize=10,handlelength=1.3,handleheight=.85,columnspacing=1.1,handletextpad=.6)
for stem in ['figure5_technician_score_distribution', 'figure5_technician_score_distribution_preview']:
    for ext in ['png','pdf']:
        fig.savefig(ROOT/f'{stem}.{ext}',facecolor='white')
plt.close(fig)
print('Verified 80 ratings per technician; scores 4–5:', counts[:,3:].sum(1).tolist())
