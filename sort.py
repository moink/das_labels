import pandas as pd

INPUT_DATA_PATH = "list.csv"
OUTPUT_DATA_PATH = "sorted_bags.csv"
SORT_ORDER = ["category_order", "size_order"]
SIZE_ORDER = {
    "XXL": 0,
    "XL": 1,
    "L": 2,
    "M": 3,
    "S": 4,
    "XS": 5,
}
CATEGORY_ORDER = {
    "Headliner": 0,
    "Festival Pass": 1,
    "Performer Pass": 2,
}

def main():
    participants = pd.read_csv(INPUT_DATA_PATH)
    participants.fillna("", inplace=True)
    # Only people receiving a T-shirt get a bag
    bags = participants[participants["T-shirt size"] != ""].copy()
    bags["category_order"] = bags["Category"].map(CATEGORY_ORDER)
    bags["size_order"] = bags["T-shirt size"].map(SIZE_ORDER)
    bags.sort_values(SORT_ORDER, inplace=True)
    bags.drop(columns=SORT_ORDER, inplace=True)
    bags.to_csv(OUTPUT_DATA_PATH, index=False)


if __name__ == "__main__":
    main()