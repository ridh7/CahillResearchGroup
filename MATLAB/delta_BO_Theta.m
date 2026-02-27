
function delta_BO_Theta=delta_BO_Theta(niu,coef,f,lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump,xoffset)

kmax=1/sqrt(r_pump^2+r_probe^2)*2; %upper integral limit
ii=sqrt(-1);
omega=2*pi*f;
alpha_down=lambda_down(3)./C_down(3);
q2=ii*omega./alpha_down;
%Computes frequency domain beam difflection theta

C_probe=0.7; % this value is obtained by calibration of coefficient of thermal expansion of CaF2
for n=1:1:length(f)
        delta_BO_Theta(n,1)=integral(@(kvect) -C_probe*8*pi^2*kvect.^2.*(-besselj(1,2.*pi.*kvect.*xoffset)).*(2.*(1+niu).*coef./(sqrt(4.*pi^2.*eta_down(3).*kvect.^2.+q2(n)) + 2*pi*kvect)).* ...
        BiFDTR_BO_TEMP(kvect,f(n),lambda_up,C_up,h_up,eta_up,lambda_down,C_down,h_down,eta_down,r_pump,r_probe,A_pump),0,kmax);
end
 
end
