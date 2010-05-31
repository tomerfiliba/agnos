#:: @const name=VOL_SIZE_DIVISOR value=17000 type=int64
VOL_SIZE_DIVISOR = 17000

def round_size(size):
    if size % VOL_SIZE_DIVISOR == 0:
        return size
    return ((size // VOL_SIZE_DIVISOR) + 1) * VOL_SIZE_DIVISOR

