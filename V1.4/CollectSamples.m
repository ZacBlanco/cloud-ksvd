function [ newIm2,newLa,index ] = CollectSamples(images,labels,scaling,numbers,samples )
%% Prelims
newIm = zeros(size(images,1),samples*length(numbers));
newLa = zeros(samples*length(numbers),1);
SamplesMatrix = samples*ones(1,length(numbers));
iter = 0;
%% Extraction Code
order = randperm(length(labels));
for iter = 1:length(labels)
        k = order(iter);
        temp = find(labels(k)==numbers);
        if (sum(SamplesMatrix)==0)
            break;
        end
        if any(temp)
            if SamplesMatrix(temp) > 0
                newIm(:,SamplesMatrix(temp)+samples*(temp-1)) = images(:,k);
                newLa(SamplesMatrix(temp)+samples*(temp-1)) = labels(k);
                SamplesMatrix(temp) = SamplesMatrix(temp)-1;
            end
        end
        if mod(k,3) == 0 
        %waitbar(tc1*(1-(sum(SamplesMatrix)/(samples*length(numbers)))),h,...
        %    [num2str(samples*length(numbers)-sum(SamplesMatrix)) ' Samples'...
        %       ' Collected, Checking image:' num2str(k)]);
        end
end

%If there's not enough images for the demanded samples
assert((sum(SamplesMatrix)==0),['Not enough images available; missing ' num2str(sum(SamplesMatrix)) ' samples'])

%% Resizing Code
if scaling ~= 1
    imRes = size(images,1).^0.5;
    newRes = round((imRes^2 * scaling)^0.5);
    
    assert(abs((imRes^2 * scaling)^0.5 - newRes)<1e-3,['Inappropriate scaling.'])
    
    for k = 1:length(newLa)
        resizedImage = imresize(reshape(newIm(:,k),imRes,imRes),sqrt(scaling));
        reshapedImage = reshape(resizedImage,newRes*newRes,1);
        newIm2(:,k) = reshapedImage';
        %waitbar(tc1+tc2*k/length(newLa),h,['Resizing image: ' num2str(k)]);
    end
else
    newIm2 = newIm;
end
index = [0:samples:(x*y)] + 1;

%close(h);
end

