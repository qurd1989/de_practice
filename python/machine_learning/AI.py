numbers = [12,4,8,15,6,10]

def total_sum(nums):
    total = 0
    for num in nums:
        total  += num
    return total
total_sum(numbers)
print(total_sum(numbers))

def average(nums):
    if len(nums) == 0:
        return 0;
    return total_sum(nums) / len(nums)
print(average(numbers))

def largest_number(nums):
    if len(nums) == 0:
        return 0;
    largest = nums[0]
    for num in nums:
        if num > largest:
            largest = num
    return largest
print(largest_number(numbers))

def smallest_number(nums):
    if len(nums) == 0:
        return 0;
    smallest = nums[0]
    for num in nums:
        if num < smallest:
            smallest = num
    return smallest

def filter_data(nums,):
    filtered_nums = []
    for num in nums:
        if num > 10:
            filtered_nums.append(num)
    return filtered_nums
print(filter_data(numbers))


employee = {
    "name": "John Doe",
    "age": 30,
    "department": "Engineering",
    "salary": 75000
}
print(employee["name"])
employee["salary"] =  employee["salary"] * 1.10
employee["location"] = "New York"
print(employee)

text = "data engineering moves data from source to destination"
word_count = {}
for word in text.split():
    if word in word_count:
        word_count[word] += 1
    else:
        word_count[word] = 1
print(word_count)

logs = [
    "Error disk full",
    "Warning CPU usage high",
    "Info backup completed",
    "Error network timeout",
    "Info user login successful",
    "Warning memory usage high",
    "Error disk full",
]

counts = {"Error": 0, "Warning": 0, "Info": 0}
for log in logs:
    level = log.split()[0]
    if level in counts:
        counts[level] += 1
print(counts)


