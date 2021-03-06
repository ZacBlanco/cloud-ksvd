%==========================================================================
%                            Cloud K-SVD Final                            %
%==========================================================================
function [nodeD,nodeX,error] = CloudKSVD(cloudY,cloudD,T0,Td,Tc,Tp)
%% Prelims
D = cloudD;
Y = cloudY;
n = size(D,1);
K = size(D,2);
N = size(D,3);
%variables are same names as described in the paper
%% Assign Nodes Local Data and Dictionaries
nodeD = D;
nodeY = Y;
%Graph info
[adj,W] = generateNetworkInfo(N);   %adjacency matrix
dref = rand(n,1);                   %common reference direction
%% Full loop
for Iteration = 1:Td
    %Sparse Coding Stage
    for i = 1:N
        nodeD(:,:,i) = normc(nodeD(:,:,i));
        nodeX(:,:,i) = full(omp(nodeD(:,:,i),nodeY(:,:,i),[],T0));
    end
    %Codebook Update Stage
    for k = 1:K
        for i = 1:N
            wk = find(nodeX(k,:,i)); %fast calc of Error below
            Ek = (nodeY(:,:,i)-nodeD(:,:,i)*nodeX(:,:,i))+nodeD(:,k,i)*nodeX(k,:,i);
            EkR= Ek(:,wk);           %selecting relevent error columns
            M(:,:,i) = EkR*EkR';     %find M
        end
        %Cloud update
        q = PowerConsensus(M,adj,Tc,Tp);
        M = [];                      %empty M, and define q(:,eachNode)
        for i = 1:N
            wk = find(nodeX(k,:,i));
            Ek = (nodeY(:,:,i)-nodeD(:,:,i)*nodeX(:,:,i))+nodeD(:,k,i)*nodeX(k,:,i);
            EkR= Ek(:,wk);           %Recalculate since we can't store
            
            if length(wk) ~= 0
                nodeD(:,k,i) = sign(dot(q(:,i),dref))*(q(:,i));
                nodeX(k,:,i) = 0;                    %clean x
                nodeX(k,wk,i) = nodeD(:,k,i)'*EkR;   %update x
            end
            error(Iteration,i) = norm(nodeY(:,:,i)-nodeD(:,:,i)*nodeX(:,:,i));
        end
    end
end
end

%% Distributed Power Method Sim
function [q] = PowerConsensus(M,W,tc,tp)
%M is an input where Mi (a 2d matrix) is defined for all nodes i = [1:N]
%tc and tp are iterations of consensus and power method, respectively
nodes = size(M,3);
datasize = size(M,1);

%simulate consensus iterations
newW = mpower(W,tc);

q = ones(datasize,nodes);
if isempty(find(sum(M,3)))         %Check if there is any error
    q = zeros(datasize,nodes);     %If there is not, all vecs are eig vecs
else
    for powermethod = 1:tp
        for i = 1:nodes
            z(:,i) = M(:,:,i)*q(:,i);
        end
        v = z*newW;
        q = normc(v);             %q is normalized locally
    end
end
end