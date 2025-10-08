from decimal import Decimal, getcontext

# Increase precision for Decimal
getcontext().prec = 28

# Origin in feet (as used earlier)
origin_feet = (Decimal('18.363337381'), Decimal('29.045044999'), Decimal('5.858191379'))

# Conversion factors
# International foot (exact): 0.3048 m
international = Decimal('0.3048')
# US survey foot (exact rational ~ 1200/3937), decimal approx
survey = Decimal('0.304800609601219202438404')

# Convert
origin_m_international = tuple((f * international) for f in origin_feet)
origin_m_survey = tuple((f * survey) for f in origin_feet)

# Differences (survey - international)
diffs = tuple((s - i) for s, i in zip(origin_m_survey, origin_m_international))

# Print with high precision
print('Feet -> Meters conversion (high precision)')
print('Origin (feet):', origin_feet)
print('\nUsing international foot (exactly 0.3048 m):')
for i, v in enumerate(origin_m_international):
    print(f'  coord {i}: {v}')

print('\nUsing US survey foot (~0.3048006096012192 m):')
for i, v in enumerate(origin_m_survey):
    print(f'  coord {i}: {v}')

print('\nDifference (survey - international) in meters:')
for i, v in enumerate(diffs):
    print(f'  coord {i}: {v}')

# Show typical float double precision values as used in code
import numpy as np
of = np.array([18.363337381, 29.045044999, 5.858191379], dtype=float)
origin_m_float = of * 0.3048
print('\nAs float (double precision) with 15+ digits:')
for i, v in enumerate(origin_m_float):
    print(f'  coord {i}: {v:.12f}')

print('\nRecommendation: use international foot factor 0.3048 (exact) unless you specifically use US survey foot.')
print('If you need more precision in outputs, increase printed decimals (e.g., to 9 or 12 decimal places).')
