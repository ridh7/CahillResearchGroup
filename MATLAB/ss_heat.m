
function ss_heat=ss_heat(lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump)

kmax=1/sqrt(r_pump^2+r_probe^2)*2; %upper integral limit
kmin=1/(10000*max(r_pump,r_probe));

f=0;

%Computes temperature at zero frequency
 
    ss_heat=rombint(@(kvect) ...
        kvect.*BiFDTR_BO_TEMP(kvect,f,lambda_up,C_up,h_up,eta_up,lambda_down,C_down,h_down,eta_down,r_pump,r_probe,A_pump),kmin,kmax);
 
end
