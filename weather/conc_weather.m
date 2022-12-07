% select folder with weather_data
folder='/Users/lukaschagas/Desktop/weather_python/gesamt11'; 
cd(folder);
d=dir(folder);
e={d.name};
% filter for documents with xls extension
%The url of the weather station is in its name 
f=e(~cellfun(@isempty,regexp(e,'.+(?=\.xls)','match')));
opts = spreadsheetImportOptions("NumVariables", 30);
opts.DataRange = "A8";
%select Variables of Interest and of which type they are
opts.VariableNames = ["Localtime", "T", "Po", "P", "Pa", "U", "DD", "Ff", "ff10", "ff3", "N", "WW", "W1", "W2", "Tn", "Tx", "Cl", "Nh", "H", "Cm", "Ch", "VV", "Td", "RRR", "tR", "E", "Tg", "E1", "sss", "URL"];
opts.VariableTypes = ["string", "double", "double", "double", "string", "double", "string", "double", "double", "string", "categorical", "string", "string", "string", "double", "double", "string", "string", "categorical", "string", "string", "double", "double", "string", "double", "string", "string", "string", "string", "string"];
opts = setvaropts(opts, ["Pa", "DD", "ff3", "WW", "W1", "W2", "Cl", "Nh", "Cm", "Ch", "RRR", "E", "Tg", "E1", "sss", "URL"], "WhitespaceRule", "preserve");
opts = setvaropts(opts, ["Pa", "DD", "ff3", "N", "WW", "W1", "W2", "Cl", "Nh", "H", "Cm", "Ch", "RRR", "E", "Tg", "E1", "sss", "URL"], "EmptyFieldRule", "auto");

%Import Data
for k=1:numel(f)
  data{k,1}=readtable(f{k}, opts, "UseExcel", false);

end
%Create new URL variable with file name as input
for k=1:numel(f)
     data{k,1}.URL = string(repmat(e{k+3},height(data{k,1}),1)); 
end
weather_italy1=vertcat(data{1:numel(f)});

%Rename Variables
weather_italy1.Properties.VariableNames{'Localtime'} = 'date';
weather_italy1.Properties.VariableNames{'T'} = 'temp_mean_c';
weather_italy1.Properties.VariableNames{'U'} = 'hum_mean_perc';
weather_italy1.Properties.VariableNames{'Tn'} = 'temp_min_c';
weather_italy1.Properties.VariableNames{'Tx'} = 'temp_max_c';
weather_italy1.Properties.VariableNames{'RRR'} = 'prec_total_mm';

data{k,1}.URL = e{i+3} % namen fangen an 4. stelle an
