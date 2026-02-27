function [delta_norl,fitresult]=FDTR_FIT_inout(X,Vcorrected_in,Vcorrected_out, ...
    niu,f2,lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump,xoffset)

f=f2(:,1);
lambda_down(3)=X(1);
coef=X(2);

delta_Theta=delta_BO_Theta(niu,coef,f,lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump,xoffset);
delta_outofphase=imag(delta_Theta);
delta_inphase=real(delta_Theta);
delta_all=[delta_outofphase,delta_inphase];
delta_norl=delta_all./[max(abs(Vcorrected_in)),3.0*max(abs(Vcorrected_in))];

fitresult=X
