

def calc_average_precision(input):
    precisions = []
    s = 0
    for idx, v in enumerate(input):
        if v == 1 or str(v).lower() == 'true':
            s += 1  
            p = s * 1.0 / (idx+1)

            precisions.append(p)
    
    return sum(precisions) / len(precisions) if len(precisions) > 0 else 0

def calc_reciprocal_rank(input):
    for idx, v in enumerate(input):
        if v == 1 or str(v).lower() == 'true':
            break
    
    return 1.0 / (idx + 1) if idx < len(input) else 0

def calc_precision(input):
    s = 0
    for v in input:
        if v == 1 or str(v).lower() == 'true':
            s += 1
    return s * 1.0 / len(input)


def main():
    with open('queries2.txt') as fin, open("rq3_2.csv", "w") as fout:
        lines = fin.readlines()
        num = len(lines) / 4
        for i in range(num):
            query = lines[4*i].strip()
            our = lines[4*i+1].strip().split()
            baseline = lines[4*i+2].strip().split()

            print query
            our_precisions = [calc_precision(our[0:5]), calc_precision(our[0:10]), calc_precision(our[0:20])]
            baseline_precisions = [calc_precision(baseline[0:5]), calc_precision(baseline[0:10]), calc_precision(baseline[0:20])]
            
            our_aps = [calc_average_precision(our[0:5]), calc_average_precision(our[0:10]), calc_average_precision(our)]
            baseline_aps = [calc_average_precision(baseline[0:5]), calc_average_precision(baseline[0:10]), calc_average_precision(baseline)]

            our_rrs = [calc_reciprocal_rank(our[0:5]), calc_reciprocal_rank(our[0:10]), calc_reciprocal_rank(our[0:20])]
            baseline_rrs = [calc_reciprocal_rank(baseline[0:5]), calc_reciprocal_rank(baseline[0:10]), calc_reciprocal_rank(baseline[0:20])]

            fout.write('%s,%s\n' % (query, ','.join([str(v) for v in our_precisions+baseline_precisions+our_aps+baseline_aps+our_rrs+baseline_rrs])))




if __name__ == '__main__':
    main()
