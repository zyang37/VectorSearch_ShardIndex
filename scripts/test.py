import asyncio

class Loader:
    def __init__(self, interval=1):
        self.interval = interval  # Interval in seconds between operations
        self.running = False  # Control flag to stop the loop

    async def load_data(self):
        """Simulated task that runs repeatedly in the background."""
        self.running = True
        try:
            while self.running:
                print("Loading data...")
                await asyncio.sleep(self.interval)  # Simulate the time-consuming task
                print("Data loaded.")
        finally:
            print("Loader has been stopped.")

    def start(self):
        """Start the background task."""
        asyncio.create_task(self.load_data())

    def stop(self):
        """Stop the background task."""
        self.running = False

async def perform_other_tasks(duration, interval):
    """Simulates other operations that occur in the main function."""
    end_time = asyncio.get_running_loop().time() + duration
    while asyncio.get_running_loop().time() < end_time:
        print("Performing other tasks...")
        await asyncio.sleep(interval)  # Wait for interval then do the task again
        print("Other tasks done.")

async def main():
    loader = Loader(interval=2)
    loader.start()  # Start the loader in the background

    # Simulate other operations in the main function
    await perform_other_tasks(5, 1)  # Perform tasks for 5 seconds, printing every 1 second
    print("Main tasks are running concurrently...")

    # Stop the loader after some time
    loader.stop()
    await asyncio.sleep(1)  # Allow some time to see the loader stopping

    print("Main function is done.")

# Running the main coroutine
asyncio.run(main())
