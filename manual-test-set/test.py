import json

# Read the JSON file
with open("solved.json", "r") as file:
    data = json.load(file)

# Extract the solution grid
grid = data["body"]
# Handle double-encoded JSON
if isinstance(grid, str):
    grid = json.loads(grid)["solution_grid"]

# Counters
text_count = 0
question_count = 0
total_count = 0

# Function to print the crossword nicely
def print_crossword(grid):
    for row in grid:
        line = []
        for cell in row:
            if cell:
                line.append(cell)
                total_count_local[0] += 1
                if cell == "?":
                    question_count_local[0] += 1
                else:
                    text_count_local[0] += 1
            else:
                line.append(".")
        print(" ".join(line))

# Use lists to allow modification inside the function
text_count_local = [0]
question_count_local = [0]
total_count_local = [0]

# Print the grid and count
print_crossword(grid)

# Get counts from function
text_count = text_count_local[0]
question_count = question_count_local[0]
total_count = total_count_local[0]

print("\nCounts:")
print(f"Text squares (letters): {text_count}")
print(f"'?' squares: {question_count}")
print(f"Total filled squares: {total_count}")
