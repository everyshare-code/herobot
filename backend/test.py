response = "{aas}dsada}"
start = response.index("{")
end = response.rindex("}")
print(response[start: end])

