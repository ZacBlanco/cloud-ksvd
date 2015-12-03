function [  ] = showImage( imagematrix,col )
imsiz = ceil(size(imagematrix,1).^0.5);
reshaped = reshape(imagematrix(:,col),imsiz,imsiz);
newimage = imresize(reshaped,10);
imshow(newimage);
end


