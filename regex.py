import re

bowled = re.compile(r'^b ([\w\s]+)')
caught = re.compile(r'c ([\w\s]+) b ([\w\s]+)')
lbw = re.compile(r'lbw b ([\w\s]+)')
st = re.compile(r'st ([\w\s]+) b ([\w\s]+)')
caught_and_bowled = re.compile(r'c and b ([\w\s]+)')
run_out = re.compile(r'run out \(([\w\s]+)/?([\w\s]+)?\)')

remove_captain_and_wk = re.compile(r'([^\s]+) \((wk|c|c & wk)\)')