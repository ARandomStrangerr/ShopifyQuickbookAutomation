import time
import sys

# Define the spinner characters to simulate a spinning clock
spinner = ['|', '/', '-', '\\']

# How long you want the spinner to run (in seconds)
duration = 5
end_time = time.time() + duration

# Loop until the time is up
while time.time() < end_time:
    for symbol in spinner:
        sys.stdout.write(f'\rSpinning Clock: {symbol}')  # '\r' returns cursor to the start of the line
        sys.stdout.flush()  # Forces the output to be written
        time.sleep(0.1)  # Wait for 0.1 second before moving to the next frame

# Clear the spinner after completion
sys.stdout.write('\rDone!           \n')

