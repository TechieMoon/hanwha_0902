def fibonacci_sequence(n):
    fib_seq = [1, 1]  # Starting with first two terms as 1, 1
    while len(fib_seq) < n:
        fib_seq.append(fib_seq[-1] + fib_seq[-2])
    return fib_seq

# Example usage: Generate first 10 Fibonacci numbers
print(fibonacci_sequence(10))
