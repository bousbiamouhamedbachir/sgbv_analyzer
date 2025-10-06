import requests
from bs4 import BeautifulSoup
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA


def scrape():
    url = "https://www.sgbv.dz/?page=detail_creance&lang=eng"
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"class": "table"})
    
    def parse_value(val: str):
        if val == "NC" or val == "-":
            return 0
        clean = val.replace(" ", "").replace(",", ".")
        try:
            if "." in clean:
                return float(clean)
            else:
                return int(clean)
        except ValueError:
            return val
    
    matrix = []
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            cols_text = [col.get_text(strip=True) for col in cols]
            if cols_text:
                parsed = [parse_value(v) for v in cols_text]
                matrix.append(parsed)
    
    return matrix[1:] if len(matrix) > 1 else []


def analyze(matrix):
    """
    Improved analysis with PCA, TOPSIS, and non-linear weighting.
    """
    numeric_data = []
    for row in matrix:
        opening = row[2]
        closing = row[3] if row[3] != 0 else row[2]
        change = row[4]
        monthly = row[5]
        annual = row[6]
        pe = row[7]
        dividend = row[8]
        volume = row[9]
        value = row[10]

        numeric_data.append([opening, closing, change, monthly, annual, pe, dividend, volume, value])

    X = np.array(numeric_data, dtype=float)

    # Normalize
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # ---------- (1) PCA-based score ----------
    pca = PCA(n_components=1)
    pca_scores = pca.fit_transform(X_scaled).flatten()

    # ---------- (2) TOPSIS scoring ----------
    # Ideal best (max for benefit, min for cost)
    benefit_idx = [2, 3, 4, 6, 7, 8]  # change%, monthly, annual, dividend, volume, value
    cost_idx = [0, 1, 5]              # opening, closing, P/E
    
    ideal_best = np.max(X_scaled, axis=0)
    ideal_worst = np.min(X_scaled, axis=0)

    # Adjust for cost criteria (reverse them)
    for i in cost_idx:
        ideal_best[i], ideal_worst[i] = ideal_worst[i], ideal_best[i]

    # Euclidean distances
    dist_best = np.linalg.norm(X_scaled - ideal_best, axis=1)
    dist_worst = np.linalg.norm(X_scaled - ideal_worst, axis=1)
    topsis_scores = dist_worst / (dist_best + dist_worst)

    # ---------- (3) Non-linear weighting ----------
    weights = np.array([
        -0.2,  # Opening
        -0.2,  # Closing
        -0.2,  # Change %
        0.2,   # Monthly % Change
        0.2,   # Annual % Change
        -0.2,  # P/E (to be penalized non-linearly below)
        0.2,   # Dividend Yield
        0.2,   # Volume
        0.2    # Value
    ])

    weighted_scores = X_scaled @ weights

    # Non-linear penalty for high P/E ratios
    pe_column = X[:, 5]
    pe_penalty = np.tanh(pe_column / 50)  # smoothly increases with high P/E
    weighted_scores -= pe_penalty

    # ---------- Combine all scores ----------
    # Normalize scores before averaging
    def normalize(arr):
        return (arr - arr.min()) / (arr.max() - arr.min() + 1e-9)

    pca_norm = normalize(pca_scores)
    topsis_norm = normalize(topsis_scores)
    weighted_norm = normalize(weighted_scores)

    final_score = (pca_norm + topsis_norm + weighted_norm) / 3

    # Append score to matrix
    for i, row in enumerate(matrix):
        row.append(float(final_score[i]))

    # Sort by score
    matrix_sorted = sorted(matrix, key=lambda r: r[-1], reverse=True)

    return matrix_sorted


# Example usage
if __name__ == "__main__":
    ranked_matrix = analyze(scrape())
    for row in ranked_matrix:
        print(row)
