%% Initialize Data

CollectData; %also included in AllSamples.mat
clc

%% Analysis

corr_values = corrcoef(DataSignals'); %OLS, finds Beta1
runtime_corr = corr_values(end,:)'; %how above vars affect run time

correlation_with_runtime = [DataSignalVars,num2cell(runtime_corr)]

for k = 1:size(runtime_corr,2)
    if runtime_corr(k) < 0
        disp(['Warning: Increasing ' cell2mat(DataSignalVars(k))...
             ' decreases run time'])
    end %generally, increasing these parameters should increase run time
end

% Feature analysis simpler with DataSignals matrix to better determine
% effects of variables on run time