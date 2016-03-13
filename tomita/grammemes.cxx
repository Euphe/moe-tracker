#encoding "utf-8"    // сообщаем парсеру о том, в какой кодировке написана грамматика
#GRAMMAR_ROOT ROOT     // указываем корневой нетерминал грамматики


A -> AnyWord<gram="A"> interp(A.Name);
ADV -> AnyWord<gram="ADV"> interp(ADV.Name);
ADVPRO -> AnyWord<gram="ADVPRO"> interp(ADVPRO.Name);
ANUM -> AnyWord<gram="ANUM"> interp(ANUM.Name);
APRO -> AnyWord<gram="APRO"> interp(APRO.Name);
//COM -> AnyWord<gram="COM"> interp(COM.Name);
//CONJ -> AnyWord<gram="CONJ"> interp(CONJ.Name);
INTJ ->  AnyWord<gram="INTJ"> interp(INTJ.Name);
//NUM -> AnyWord<wff=/(\d+)/> interp(NUM.Name) | AnyWord<gram="NUM"> interp(NUM.Name);
//PART -> AnyWord<gram="PART"> interp(PART.Name);
//PR -> AnyWord<gram="PR"> interp(PR.Name);
//SPRO ->  AnyWord<gram="SPRO"> interp(SPRO.Name);
V -> AnyWord<gram="V"> interp(V.Name);
S -> AnyWord<gram="S"> interp(S.Name);
ROOT -> S | A | ADV | ADVPRO | ANUM | APRO | INTJ  | V;