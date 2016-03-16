function [ adjacencymatrix ] = generateNodes( size )
P = ((2/size).^0.6);  %probability of connection chosen to consistently
if size == 1          %generate very sparsely connected graphs quickly
    adjacencymatrix = 1;
    return;
else
    A = zeros(size);
    for i = 1:size
        for j = 1:(i-1)      %nodes assumed to be connected to themselves
            if rand() < P    %biased "coin flip" to add nodes
                A(i,j) = 1;  %add bidirectional nodes since mesh network
                A(j,i) = 1;  %can send or receive data
            end
        end
    end
    if (~checkNodeConnectivity(A))
        A = generateNodes(size);
    end
    adjacencymatrix = A;
end
end
