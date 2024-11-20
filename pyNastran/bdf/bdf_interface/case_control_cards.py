#from .subcase_cards_check import
from .subcase.cards import (
    GROUNDCHECK, EXTSEOUT, WEIGHTCHECK, DSAPRT, MEFFMASS,
    MODCON, SET, SETMC, SUPER, SEALL, SEDR, HARMONICS, AEROF, APRES,
    CSCALE, GPKE, GPRSORT, GPSDCON, GPSTRESS, OFREQUENCY, OMODES, SURFACE, VOLUME,
)
from .subcase.cards_str import (
    AECONFIG, ANALYSIS, AUTOSPC, AESYMXY, AESYMXZ, AXISYMMETRIC,
    DSYM, ECHO, SEQDEP, K2PP, THERMAL, RIGID,
)
from .subcase.cards_int import (
    ADACT, ADAPT, AUXMODEL,
    BC, BCONTACT, BCSET, BGSET, BOLTLD,
    CLOAD, CMETHOD, CSSCHD,
    DESOBJ, DESGLB, DESSUB, DLOAD, DIVERG, DRSPAN, DYNRED,
    EBDSET, ELAR,
    FMETHOD, FREQUENCY, GUST, IC,
    LINE, LOAD, LOADSET,
    MFLUID, MODES, MODTRAK, MPC, MAXLINES, METHOD, MODESELECT,
    NLCNTL, NONLINEAR, NSM, NLPARM, NLPCI,
    OTIME, OMODES, OUTRCV, PARTN, RGYRO, RMETHOD, RSMETHOD,
    SEFINAL, SMETHOD, STATSUB, SUPORT1, SYM, SYMCOM, SDAMPING, SPC, SEDV,
    TFL, TSTEP, TSTEPNL, TRIM, TSTRU, RANDOM,
)
from .subcase.cards_check import (
    DATAREC, DISPLACEMENT, VELOCITY, ACCELERATION,
    SDISPLACEMENT, SVELOCITY, SACCELERATION, SVECTOR,
    MPCFORCES, SPCFORCES, OLOAD,
    STRESS, STRAIN, FORCE, EDE, ESE, GPFORCE,
    TEMPERATURE, THERMAL, ENTHALPY, FLUX,
    RESVEC,
    ELSUM, GPSDCON, GPSTRAIN, GPSTRESS,
    NLLOAD, NLSTRESS, NOUTPUT, OPRESS, OTEMP, STRFIELD, ELSDCON,
    BOUTPUT, BGRESULTS, PRESSURE, SENSITY,
)

#STATSUB
CLASS_MAP = {

    # int/str/options
    'DISPLACEMENT' : DISPLACEMENT,
    'VELOCITY' : VELOCITY,
    'ACCELERATION' : ACCELERATION,
    'SDISPLACEMENT' : SDISPLACEMENT,
    'SVELOCITY' : SVELOCITY,
    'SACCELERATION' : SACCELERATION,
    'SVECTOR' : SVECTOR,
    'MPCFORCES' : MPCFORCES,
    'SPCFORCES' : SPCFORCES,
    'OLOAD' : OLOAD,
    'STRESS' : STRESS,
    'STRAIN' : STRAIN,
    'FORCE' : FORCE,
    'EDE' : EDE,
    'ESE' : ESE,
    'GPFORCE' : GPFORCE,
    'TEMPERATURE' : TEMPERATURE,
    'THERMAL' : THERMAL,
    'ENTHALPY' : ENTHALPY,
    'FLUX' : FLUX,
    'RESVEC' : RESVEC,
    'ELSUM' : ELSUM,
    'GPSDCON' : GPSDCON,
    'GPSTRAIN' : GPSTRAIN,
    'GPSTRESS' : GPSTRESS,
    'NLLOAD' : NLLOAD,
    'NLSTRESS' : NLSTRESS,
    'NOUTPUT' : NOUTPUT,
    'OPRESS' : OPRESS,
    'OTEMP' : OTEMP,
    'STRFIELD' : STRFIELD,
    'ELSDCON' : ELSDCON,
    'BOUTPUT' : BOUTPUT,
    'BGRESULTS' : BGRESULTS,
    'PRESSURE' : PRESSURE,
    'SENSITY' : SENSITY,

    # int/str
    'OFREQUENCY' : OFREQUENCY,

    # sets
    'SET' : SET,
    'SETMC' : SETMC,

    # int
    'ADACT' : ADACT,
    'ADAPT' : ADAPT,
    'AUXMODEL' : AUXMODEL,
    'BC' : BC,
    'BCONTACT' : BCONTACT,
    'BCSET' : BCSET,
    'BGSET' : BGSET,
    'BOLTLD' : BOLTLD,
    'CLOAD' : CLOAD,
    'CMETHOD' : CMETHOD,
    'CSSCHD' : CSSCHD,
    'DATAREC' : DATAREC,
    'DLOAD' : DLOAD,
    'DESGLB' : DESGLB,
    'DESOBJ' : DESOBJ,
    'DESSUB' : DESSUB,
    'DRSPAN' : DRSPAN,
    'DIVERG' : DIVERG,
    'DYNRED' : DYNRED,
    'EBDSET' : EBDSET,
    'ELAR' : ELAR,
    'FREQUENCY' : FREQUENCY,
    'GUST' : GUST,
    'IC' : IC,
    'FMETHOD' : FMETHOD, # FLUTTER
    'LINE' : LINE,
    'LOAD' : LOAD,
    'LOADSET' : LOADSET,
    'MAXLINES' : MAXLINES,
    'MFLUID' : MFLUID,
    'MODES' : MODES,
    'MODTRAK' : MODTRAK,
    'MODESELECT' : MODESELECT,
    'MPC' : MPC,
    'METHOD' : METHOD,
    'NLCNTL' : NLCNTL,
    'NONLINEAR' : NONLINEAR,
    'NSM' : NSM,
    'NLPARM' : NLPARM,
    'NLPCI' : NLPCI,
    'OUTRCV' : OUTRCV,
    'OTIME' : OTIME,
    'OMODES' : OMODES,
    'PARTN' : PARTN,
    'RGYRO' : RGYRO,
    'RMETHOD' : RMETHOD,
    'RSMETHOD' : RSMETHOD,
    'SEFINAL' : SEFINAL,
    'SMETHOD' : SMETHOD,
    'STATSUB' : STATSUB,
    'SUPORT1' : SUPORT1,
    'SYM' : SYM,
    'SYMCOM' : SYMCOM,
    'SDAMPING' : SDAMPING,
    'SPC' : SPC,
    'SEDV' : SEDV,
    'TFL' : TFL,
    'TRIM' : TRIM,
    'TSTEP' : TSTEP,
    'TSTEPNL' : TSTEPNL,
    'TSTRU' : TSTRU,
    'RANDOM' : RANDOM,

    # string cards
    'AECONFIG' : AECONFIG,
    'AUTOSPC' : AUTOSPC,
    'ANALYSIS' : ANALYSIS,
    'ECHO' : ECHO,
    'AESYMXY' : AESYMXY,
    'AESYMXZ' : AESYMXZ,
    'AXISYMMETRIC' : AXISYMMETRIC,
    'DSYM' : DSYM,
    'SEQDEP' : SEQDEP,
    'K2PP' : K2PP,
    'RIGID' : RIGID,

    #  other??
    'SUPER' : SUPER,
    'SEALL' : SEALL,
    'SEDR' : SEDR,

    'HARMONICS' : HARMONICS,
    'AEROF' : AEROF,
    'APRES' : APRES,

    'CSCALE' : CSCALE,
    'GPKE' : GPKE,
    'GPRSORT' : GPRSORT,
    'SURFACE' : SURFACE,
    'VOLUME' : VOLUME,

    # weird; multi-equals
    'GROUNDCHECK' : GROUNDCHECK,
    'EXTSEOUT' : EXTSEOUT,
    'WEIGHTCHECK' : WEIGHTCHECK,
    'DSAPRT' : DSAPRT,
    'MODCON' : MODCON,
    'MEFFMASS' : MEFFMASS,

    # space separated
    #'VOLUME' : VOLUME,
    #'SURFACE' : SURFACE,
}

CLASS_MAP2 = {}
CLASS_MAP_NAMES = []
for name, card in CLASS_MAP.items():
    CLASS_MAP2[name] = card
    CLASS_MAP_NAMES.append(name)
    if hasattr(card, 'alternate_names'):
        for namei in card.alternate_names:
            CLASS_MAP2[namei] = card
            CLASS_MAP_NAMES.append(namei)
CLASS_MAP = CLASS_MAP2
CLASS_MAP_NAMES = tuple(CLASS_MAP_NAMES)
del CLASS_MAP2
