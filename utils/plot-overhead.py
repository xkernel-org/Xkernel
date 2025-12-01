#!/usr/bin/env python3
import sys
import pandas as pd
import matplotlib.pyplot as plt

def main():
    if len(sys.argv) == 1:
        csv_file = 'kernel-results/overhead.csv'
    else:
        csv_file = sys.argv[1]

    # Read CSV (header optional)
    df = pd.read_csv(csv_file)

    if df.shape[1] < 3:
        print("CSV must have at least 3 columns")
        sys.exit(1)

    # Use 2nd and 3rd columns (index 1 and 2)
    x = df.iloc[:, 1]
    y = df.iloc[:, 2]

    plt.scatter(x, y)
    plt.ylabel('Number of Lines in Dataflow Analaysis Results')
    plt.xlabel('Analysis Time (min)')
    plt.grid(True)
    plt.savefig('kernel-results/overhead.png', dpi=300, bbox_inches='tight', metadata={'CreationDate': None})

if __name__ == "__main__":
    main()
