import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

data = {
    'MAX_SOFTIRQ_RESTART': [1, 1, 1, 5, 5, 5, 10, 10, 10, 15, 15, 15, 20, 20, 20],
    'MAX_SOFTIRQ_TIME': ['1ms', '4ms', '2ms (default)', '2ms (default)', '1ms', '4ms', 
                         '2ms (default)', '1ms', '4ms', '2ms (default)', '1ms', '4ms', 
                         '2ms (default)', '1ms', '4ms'],
    'Worst latency (us)': [143, 139, 149, 265, 247, 295, 560, 357, 382, 584, 564, 505, 793, 571, 837],
    'Average latency (us)': [13, 13, 13, 14, 13, 13, 15, 14, 13, 14, 13, 14, 14, 13, 14],
    'Throughput (25Gbps)': ['23Gbps'] * 15,
    'CPU Usage': ['74%', '69%', '70%', '66%', '62%', '61%', '52%', '61%', '50%', '51%', '51%', '45%', '45%', '51%', '47%']
}
df = pd.DataFrame(data)

df['CPU Usage'] = df['CPU Usage'].str.rstrip('%').astype('float')

df['time_num'] = df['MAX_SOFTIRQ_TIME'].str.extract(r'(\d+)').astype(int)

df['MAX_SOFTIRQ_TIME'] = pd.Categorical(
    df['MAX_SOFTIRQ_TIME'],
    categories=['1ms', '2ms (default)', '4ms'],
    ordered=True
)

# 1. 绘制Worst Latency图
plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x='MAX_SOFTIRQ_RESTART', y='Worst latency (us)', 
             hue='MAX_SOFTIRQ_TIME', style='MAX_SOFTIRQ_TIME', 
             markers=True, palette='tab10')

plt.xlabel('MAX_SOFTIRQ_RESTART')
plt.xticks(df['MAX_SOFTIRQ_RESTART'].unique())
plt.ylabel('Worst Latency (us)')
plt.legend(title='MAX_SOFTIRQ_TIME')
plt.show()

# 2. 绘制CPU Usage图
plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x='MAX_SOFTIRQ_RESTART', y='CPU Usage', 
             hue='MAX_SOFTIRQ_TIME', style='MAX_SOFTIRQ_TIME', 
             markers=True, palette='tab10')

plt.xlabel('MAX_SOFTIRQ_RESTART')
plt.xticks(df['MAX_SOFTIRQ_RESTART'].unique())
plt.ylabel('CPU Usage (%)')
plt.legend(title='MAX_SOFTIRQ_TIME')
plt.show()
    