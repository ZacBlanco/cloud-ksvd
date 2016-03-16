function [ connected ] = checkNodes( adjacency )

[rows,columns] = size(adjacency);
tempsum = adjacency;
for i = 2:rows
    
    tempsum = tempsum + mpower(adjacency,i);

end

if sum(tempsum(:)==0) == 0
    
    connected = true;
else
    connected = false;
end

    

end

