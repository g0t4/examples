# %% cell1
foo = 1
bar = 2

print("foo + bar")

# %% cell2

print(foo+bar)

# %%

import matplotlib.pyplot as plt

# Sample data
x = [1, 2, 3, 4, 5]
y = [2, 3, 5, 7, 11]

# Create a figure and axis
fig, ax = plt.subplots()

# Plot the data
ax.plot(x, y)

# Display the plot
plt.show()
