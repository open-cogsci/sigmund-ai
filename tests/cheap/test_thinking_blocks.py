import pytest
from sigmund.model._base_model import BaseModel


def test_extract_thinking_blocks():
    s = '''<div class="thinking_block_signature">ErEIClsIDBgCKkCW8Br0Nu9KPkUEwHpS/eBWY9c+jXH/AY5K55c/HwHYsMsHVwQvrGW+G0V31W3XtUVNh+tLRGbYKemnsnrVkimzMhFjbGF1ZGUtc29ubmV0LTQtNjgAEgxWUM2kMcururSfnq0aDH7Snk/w6wnhCIGjLyIwTeH2H8kWoaBbrZQ8iPICqvdd5VlN9kVFE2N2CmTu43MoMEynOowt5/VSIUpxM/+uKoMH41kQuUjYnEZCG1Zc7AEed3pIxQpv2dfZakCcZ7bklfBrjx9hzwqUtmdcwgqyUlVp8oBASTe/xyEQOOVUnEh4JmVpKRA8/djEYesj5d0L65X0XbofVjO8H+bMYRv7sLeIQUYL4jLZp9QNjHEFUin2lIzdKg2k/JRJIlXUVVRSC2xvvJYE3eHvZxIszchbAd04Kxsg4d2j0PDxe3YYg233ARz6sYG7DI0gZ6oa89ElFl/H1XvCKDQduT81hflTP/2YRdz99wIdDdFcrJAXOsCPcP3Zg8Os+WYWPWCKXj4DmqGpMFVwvqdGh0ZBzzuUSn0U6eaf53sptbayHcNqCc+gNMfSLo6rBv/fNMjtGYDt7mzStjTRoPKByHkqA2vL0muWrbu8ELVfQ1u0fgyQ4AlhsapVG2ldGfNgD+rP1YzfIVPb9pQivmvWqJVwPyIM5c3Ot1gCDEAoiraANRygEypGKcE5EH0j8Yt2oeAWHPzRaMYpFt6fgjmL1hSssEOuleOyo1NEAE2FTn7UYKHyfSNcKrsAQw9EhXBj9BWIZLcFxGopUlLtW1z2Whs+k09TXL3f9canOi5DuivD6ZcgYhI+Mvv8mUFiUegd5wFs3KkH2M7NtzQJJWmy09phY99ZltncFif3dmp/PXKP7qLXQOLz9h3pN6i4EkloP8CGEfrnCB895WxC/ysg1rz7IzPNpd4RnHvqDHaARzkctFvMCPOxDaiCQoj0WRJMn7XuWDqCfY+jeOV1ziyigqMlBdDPMeidOAk2G8P2CKnaWiLW1uSKT+nxSuz9/Y+7HOSFKHePV4s113xJtkx+wfe+MViYZI6RXj7soOkCvxcL+Z5/MI5E2efW9Th4suC38OfriT27CcTmhikpGtG7dx0jKo8852o9GTnEa9RilNuYr4u7LS4Zgjzw55lQNVDPXXg2bOs2JH+eeFLUbO653NpiIni3HO3lKXOjcD/O85nIJL37dkEEyxSOcjfeIpoewk8kow28xwbe4OrY6khvr5F+jMdq/IYN6N9a3ZbL81sTE9u0pmcsVOQTSa9Wj7RAdz3Mq1TKWPm2fM/7iMa5gdMBTyA1dhpbMJ9/Gt1Bwkdsq57+nQAqHuZjccEjRF6JBV8oJe4zfiNBgF8Pi07dhN+5XuVGfFtEikYGj5E37m/knDGF0Y7JzRHtW4kAG/tJ/Nf8WBuJZOh9aUgYAQ==</div><div class="thinking_block_content">The user wants to see how I think through a simple toy problem. I'll pick a fun, classic toy problem and walk through my reasoning step by step. Let me choose something like "FizzBuzz" or a simple algorithm problem. I'll demonstrate my thought process clearly.

Let me pick a classic: finding the largest number in a list. Or maybe something slightly more interesting like FizzBuzz. Let me go with a fun one - maybe "find all prime numbers up to N" (Sieve of Eratosthenes) or something like reversing a string.

Actually, let me pick something that shows interesting reasoning - like solving the classic "Two Sum" problem, or maybe something even simpler and more visual.


I'll go with FizzBuzz since it's a great way to show step-by-step reasoning, and I'll walk through the logic before showing the implementation.</div>
Sure! Let's walk through the classic **FizzBuzz** problem — simple enough to follow, but with just enough nuance to show real thinking. 🧠

---

**The Problem:**
> Print numbers from 1 to N. But for multiples of 3, print `"Fizz"`. For multiples of 5, print `"Buzz"`. For multiples of *both*, print `"FizzBuzz"`.

---

**How I think through it:**

1. **Identify the cases.** There are 4 possible outputs: `"FizzBuzz"`, `"Fizz"`, `"Buzz"`, or the number itself.

2. **Watch out for order!** The tricky part is that the `"FizzBuzz"` case (divisible by *both* 3 and 5) must be checked **first**. If I check for 3 or 5 individually first, I'll never reach the combined case.

3. **The divisibility check** uses the modulo operator ```%```. If ```n % 3 == 0```, the number is divisible by 3.

4. **Chain the conditions** from most specific → least specific:
   - Both 3 and 5? → `"FizzBuzz"`
   - Only 3? → `"Fizz"`
   - Only 5? → `"Buzz"`
   - Neither? → the number

5. **Wrap it in a loop** from 1 to N (inclusive).

Here's the result! 👇



---

The key insight here is **ordering your conditions from most specific to least specific** — a general principle that applies far beyond FizzBuzz! 🎯

Want me to walk through a different kind of problem, like a sorting algorithm, a math puzzle, or something else?'''
    l = BaseModel.extract_thinking_blocks(s)
    assert len(l) == 2
    assert l[0]['type'] == 'thinking'
    assert l[1]['type'] == 'text'

