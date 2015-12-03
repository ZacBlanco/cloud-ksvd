function [D,x,error] = CentralKSVD(Y,D,T0,Td)
%% Vars
D = normc(D);
K = size(D,2);
h = waitbar(0,'Running KSVD...');
%% The Loop
for iteration = 1:Td
    %% SparseCodingStage
    x = full(omp(D,Y,[],T0)); %input dictionary, signals, sparsity
    %% Codebook Update
    for k = 1:K
        
        waitbar(    (k/K)/Td + (iteration-1)/Td,h,...
            ['Iteration ' num2str(iteration) ': Updating atom ' num2str(k)]);
        %fast error calc
        wk = find(x(k,:));
        Ek = (Y-D*x)+D(:,k)*x(k,:);
        ERk = Ek(:,wk);
        
        if ~isempty(wk)
            %svd decomp
            [U1,S1,V1] = svds(ERk,1);
            D(:,k) = normc(U1);
            x(k,wk) = (S1*V1');
        end
    end
    error(iteration,:) = norm(Y-D*x);
end
close(h)
end

