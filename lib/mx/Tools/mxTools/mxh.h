#ifndef MXH_H
#define MXH_H

/* 
  mxh.h -- Generic header file for all mx Extenstions

  This file should be included by every mx Extension header file
  and the C file.

  Copyright (c) 2000, Marc-Andre Lemburg; mailto:mal@lemburg.com
  Copyright (c) 2000-2004, eGenix.com Software GmbH; mailto:info@egenix.com
  See the documentation for further copyright information or contact
  the author.

*/

/*
  Macros to control export and import of DLL symbols.

  We use our own definitions since Python's don't allow specifying
  both imported and exported symbols at the same time; these defines
  haven't been thoroughly tested yet, patches are most welcome :-)

*/

/* Macro to "mark" a symbol for DLL export */

#if (defined(_MSC_VER) && _MSC_VER > 850		\
     || defined(__MINGW32__) || defined(__CYGWIN) || defined(__BEOS__))
# ifdef __cplusplus
#   define MX_EXPORT(type) extern "C" type __declspec(dllexport) 
# else
#   define MX_EXPORT(type) extern type __declspec(dllexport) 
# endif
#elif defined(__WATCOMC__)
#   define MX_EXPORT(type) extern type __export 
#elif defined(__IBMC__)
#   define MX_EXPORT(type) extern type _Export
#else
#   define MX_EXPORT(type) extern type
#endif

/* Macro to "mark" a symbol for DLL import */

#if defined(__BORLANDC__)
#   define MX_IMPORT(type) extern type __import
#elif (defined(_MSC_VER) && _MSC_VER > 850		\
       || defined(__MINGW32__) || defined(__CYGWIN) || defined(__BEOS__))
# ifdef __cplusplus
#   define MX_IMPORT(type) extern "C" type __declspec(dllimport)
# else
#   define MX_IMPORT(type) extern type __declspec(dllimport)
# endif

#else
#   define MX_IMPORT(type) extern type
#endif

/* EOF */
#endif
