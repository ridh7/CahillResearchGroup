function [delta_ratio,fitresult]=FDTR_FIT_ratio(X,Vcorrected_ratio, ...
    niu,f2,lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump,xoffset)

f=f2(:,1);
lambda_down(3)=X;
coef = 60e-6*65*0.19/sqrt(2); % this value does not influence the result of fitting

delta_Theta=delta_BO_Theta(niu,coef,f,lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump,xoffset);
delta_outofphase=imag(delta_Theta);
delta_inphase=real(delta_Theta);
delta_ratio = -delta_inphase./delta_outofphase;

fitresult=X
