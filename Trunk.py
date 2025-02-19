data: dict[str, str] = {};

def readData(fileName: str):
    file = open(fileName, "r");
    for line in file:
        arr: list[str] = line.split(":");
        data[arr[0].strip()] = arr[1].strip();
    file.close();
    return;

def writeData(fileName: str):
    val = "";
    for key, value in data.items():
        val += f"{key}:{value}\n";
    with open(fileName, "w") as file:
        file.write(val);
    return;

