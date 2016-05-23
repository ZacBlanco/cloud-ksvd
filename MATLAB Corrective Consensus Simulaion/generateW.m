function [ W ] = generateW( adjacency )

[rows,columns] = size(adjacency);

W = zeros(rows,columns); 

%Metropolis Hastings Weights
for i = 1:rows
    for j = 1:columns
        if (i~=j && adjacency(i,j)~=0)
             W(i,j) = 1/(1 + max(sum(adjacency(i,:)),sum(adjacency(:,j))));
        elseif (i == j)
            tempsum = 0;
            for x = 1:columns
                if (x~=i && adjacency(x,j)~=0)
                   tempsum = tempsum + 1/(1 + max(sum(adjacency(x,:)),sum(adjacency(:,j))));
                end
            end
             W(i,j) = 1 - tempsum;
        else
             W(i,j) = 0;
        end
    end
end

end
