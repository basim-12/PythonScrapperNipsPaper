import pandas as pd

# Function to load and analyze metadata
def analyze_papers(csv_file):
    try:
        # Load the CSV file into a pandas DataFrame
        df = pd.read_csv(csv_file)

        # Show the first few rows of the data to understand its structure
        print("Data Preview:")
        print(df.head(), "\n")

        # Check for missing or null values in the data
        print("Missing Data:")
        print(df.isnull().sum(), "\n")

        # Ensure 'Year' is in the correct format (converting to numeric if it's not)
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

        # Check for rows with invalid 'Year' values
        invalid_years = df[df['Year'].isnull()]
        if not invalid_years.empty:
            print("Rows with invalid 'Year' values:")
            print(invalid_years, "\n")

        # How many papers were published in each year
        papers_per_year = df['Year'].value_counts().sort_index()
        print("Papers per Year:")
        print(papers_per_year, "\n")

        # Finding the top authors by counting occurrences in the 'Authors' column
        # (Assuming authors are separated by commas in a single string)
        author_series = df['Authors'].str.split(',').explode().str.strip()
        top_authors = author_series.value_counts().head(10)  # Top 10 authors
        print("Top 10 Authors:")
        print(top_authors, "\n")

        # Count the total number of unique papers
        unique_papers = df['Title'].nunique()
        print(f"Total number of unique papers: {unique_papers}\n")

        # Count the total number of papers (including possible duplicates)
        total_papers = len(df)
        print(f"Total number of papers (including duplicates): {total_papers}\n")

    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
    except pd.errors.ParserError as e:
        print(f"Error parsing the CSV file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage
csv_file = 'metaData.csv'  # Replace with your actual CSV file path
analyze_papers(csv_file)