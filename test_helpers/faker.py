from faker import Faker


# Instantiating this once so that we have a single instance across all tests allowing us to use things like .unique
# and we can guarantee that we will always have unique values even if we use things like `setUpClass`.
faker = Faker()
