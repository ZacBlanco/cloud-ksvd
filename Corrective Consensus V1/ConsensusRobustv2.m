function [x,runningAvg,error] = ConsensusRobustv2(n,dim,packetloss,iterations,k)
%Variables
n; %number of nodes
k; %number of standard iterations: corrective iterations
packetloss_lambda = packetloss; %mean packets dropped per iteration
iterations; %iterations of consensus averaging
k; %number of standard consensus iterations before correction

l = 1; %number of corrective iterations completed (starts at one for simplicity)
Adj = generateNodes(n);
Edges = find(sparse(Adj));
W   = generateW(Adj);
Adj = Adj+diag(ones(1,n));
x = rand(dim,n)*10; % Node Data
phi = zeros(n,n,dim); % Mass change data
v = phi;        % Phi tracker
runningAvg = mean(x(:,:,1),2);
error = [];


%% Corrective Consensus
%Compensates for mass loss and phi error
for t = 1:iterations
    %% Packet Loss Poisson Sim
    Adj_proper = Adj;
    packets_lost = (poissrnd(packetloss_lambda));
    disp([num2str(packets_lost) ' Packets lost at t: ' num2str(t)])
    for packetloss = 1:packets_lost
        location = Edges(ceil(rand()*length(Edges)));
        Adj(location) = 0;
    end
    
    if t ~= l*(k+1)-1
    %% Standard Iteration

        for i = 1:n
            summation = 0;
            for j = 1:n
                phi(i,j,:,t+1) = phi(i,j,:,t); %carry over previous mass
                if Adj(i,j) == 1
                    difference= x(:,j,t)-x(:,i,t);
                    summation = summation + W(i,j)*difference;       %mass from other nodes
                    phi(i,j,:,t+1) = phi(i,j,:,t+1) + reshape(W(i,j)*difference,1,1,dim,1); %add new mass
                end
            end
            x(:,i,t+1)   = x(:,i,t)+summation; %update local data
        end
        
        
    else
    %% Corrective Iteration
       
        Delta = zeros(n,n,dim);
        for i = 1:n
            for j = 1:n
                if Adj(j,i)==1
                    Delta(i,j,:) = phi(i,j,:,t) + phi(j,i,:,t);   %find difference in mass distribution
                    v(i,j,l) = 1;
                end
                phi(i,j,:,t+1) = phi(i,j,:,t)-(0.5)*Delta(i,j)*v(i,j,l); %remove difference locally (2)
            end
            x(:,i,t+1) = x(:,i,t) - reshape((0.5)*sum(Delta(i,:,:).*...
                repmat(v(i,:,l),1,1,dim)),dim,1,1);  %compensate for difference (1)
        end  %logically, we compensate (1) and then remove (2), but code is faster other way around
        l = l+1; %update number of corrective iterations
    
    end
    
    Adj = Adj_proper; %reset to original adjacency matrix/connections
    runningAvg(:,t+1) = mean(x(:,:,t+1),2); %average of current data, goal is to keep it the same
end                                     %as the initial/true average before packet loss

%% Plotting
plot([0:t],reshape(x(1,:,1:t+1),n,t+1)')
line([0,iterations],[runningAvg(1,1),runningAvg(1,1)],'LineWidth',2,'LineStyle','--')
for marks = 1:floor(iterations/(k+1))
    line([marks*(k+1)-1,marks*(k+1)-1],1.1*[min(min(min(x))),max(max(max(x)))],'LineStyle',':','Color',[0.1,0.1,0.1])
end
hold on;
plot([0:t],[runningAvg(1,:)],'r--','LineWidth',2)
axis([0,t,min(min(min(x))),max(max(max(x)))])
hold off;

end