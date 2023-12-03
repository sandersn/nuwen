#Boa:Frame:frmHand

from wxPython.wx import *
from util import *
import cfg
grammar = {}
POSen = ['#'] #this list still might better be represented as a dict to allow easier singleton enforcement
#(just set POSen['POS']=1 if it exists)

def create(parent):
    return frmHand(parent)

[wxID_FRMHAND, wxID_FRMHANDBTNADD, wxID_FRMHANDBTNDELETE, wxID_FRMHANDBTNLOAD, 
 wxID_FRMHANDBTNSAVE, wxID_FRMHANDLSTGRAMMAR, wxID_FRMHANDSTATICTEXT1, 
 wxID_FRMHANDTXTCHILDREN, wxID_FRMHANDTXTSYM, 
] = map(lambda _init_ctrls: wxNewId(), range(9))

class frmHand(wxFrame):
    def _init_utils(self):
        # generated method, don't edit
        pass

    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wxFrame.__init__(self, id=wxID_FRMHAND, name='frmHand', parent=prnt,
              pos=wxPoint(218, 120), size=wxSize(435, 415),
              style=wxDEFAULT_FRAME_STYLE, title='The Invisible Hand III')
        self._init_utils()
        self.SetClientSize(wxSize(427, 388))
        self.SetToolTipString('')

        self.staticText1 = wxStaticText(id=wxID_FRMHANDSTATICTEXT1,
              label='Symbol:', name='staticText1', parent=self, pos=wxPoint(8,
              8), size=wxSize(37, 13), style=0)

        self.txtSym = wxTextCtrl(id=wxID_FRMHANDTXTSYM, name='txtSym',
              parent=self, pos=wxPoint(48, 8), size=wxSize(100, 21),
              style=wxWANTS_CHARS | wxTAB_TRAVERSAL, value='')
        self.txtSym.SetToolTipString('')

        self.txtChildren = wxTextCtrl(id=wxID_FRMHANDTXTCHILDREN,
              name='txtChildren', parent=self, pos=wxPoint(160, 8),
              size=wxSize(256, 21), style=wxWANTS_CHARS | wxTAB_TRAVERSAL,
              value='')

        self.lstGrammar = wxListBox(choices=[], id=wxID_FRMHANDLSTGRAMMAR,
              name='lstGrammar', parent=self, pos=wxPoint(8, 40),
              size=wxSize(408, 312), style=wxTAB_TRAVERSAL,
              validator=wxDefaultValidator)
        EVT_LISTBOX(self.lstGrammar, wxID_FRMHANDLSTGRAMMAR,
              self.OnLstgrammarListbox)

        self.btnAdd = wxButton(id=wxID_FRMHANDBTNADD, label='&Add',
              name='btnAdd', parent=self, pos=wxPoint(8, 360), size=wxSize(75,
              23), style=wxTAB_TRAVERSAL)
        EVT_BUTTON(self.btnAdd, wxID_FRMHANDBTNADD, self.OnButtonaddButton)

        self.btnSave = wxButton(id=wxID_FRMHANDBTNSAVE, label='&Save',
              name='btnSave', parent=self, pos=wxPoint(264, 360),
              size=wxSize(75, 23), style=0)
        EVT_BUTTON(self.btnSave, wxID_FRMHANDBTNSAVE, self.OnButtonsaveButton)

        self.btnLoad = wxButton(id=wxID_FRMHANDBTNLOAD, label='&Load',
              name='btnLoad', parent=self, pos=wxPoint(344, 360),
              size=wxSize(75, 23), style=0)
        EVT_BUTTON(self.btnLoad, wxID_FRMHANDBTNLOAD, self.OnBtnloadButton)

        self.btnDelete = wxButton(id=wxID_FRMHANDBTNDELETE, label='&Delete',
              name='btnDelete', parent=self, pos=wxPoint(88, 360),
              size=wxSize(75, 23), style=wxTAB_TRAVERSAL)
        EVT_BUTTON(self.btnDelete, wxID_FRMHANDBTNDELETE,
              self.OnBtndeleteButton)

    def __init__(self, parent):
        self._init_ctrls(parent)

    def OnLstgrammarListbox(self, event):
        event.Skip()

    def OnButtonaddButton(self, event):
        global POSen
        if self.txtSym.GetValue() and self.txtChildren.GetValue():
            symbols = self.txtChildren.GetValue().split()
            symlist = []
            for s in symbols:
                symlist.extend(splitAdditional(s,"(){}[]|"))
            sym = cfg.parseGrammar(cfg.Symbol(cfg.Symbol.PAREN,self.txtSym.GetValue()), symlist)
            grammar[self.txtSym.GetValue()] = sym
            POSen = merge(POSen, filter_dups(sym.extractPOS()))
            self.lstGrammar.Append(`sym`, sym)
    def OnButtonsaveButton(self, event):
        event.Skip()

    def OnBtnloadButton(self, event):
        event.Skip()

    def OnBtndeleteButton(self, event):
        if self.lstGrammar.GetSelection():
            sym = self.lstGrammar.GetClientData(self.lstGrammar.GetSelection())
            del grammar[sym.sym]
            self.lstGrammar.Delete(self.lstGrammar.GetSelection())
