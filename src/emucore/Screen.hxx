#ifndef SCREEN_HXX
#define SCREEN_HXX

class OSystem;

#include "emucore/bspf/bspf.hxx"

class Screen
{
  public:
    Screen(OSystem* osystem) { myOSystem = osystem; }
    virtual ~Screen() { };

  public:
    virtual void render() { };

  protected:
    OSystem* myOSystem;
};

#endif
