import { TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { AppComponent } from './app.component';
import { KeypadDialogComponent } from './dialogs/keypad-dialog/keypad-dialog.component';
import { UpdateCodeDialogComponent } from './dialogs/update-code-dialog/update-code-dialog.component';

describe('AppComponent', () => {
  let component: AppComponent;
  let dialogSpy: jest.SpyObj<MatDialog>;

  beforeEach(async () => {
    dialogSpy = { open: jest.fn() } as any;

    await TestBed.configureTestingModule({
      imports: [AppComponent],
    })
      .overrideComponent(AppComponent, {
        set: {
          providers: [{ provide: MatDialog, useValue: dialogSpy }],
        },
      })
      .compileComponents();

    const fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should have a stream URL', () => {
    expect(component.streamUrl).toContain('/api/video/stream');
  });

  it('should have 6 buttons defined', () => {
    expect(component.buttons.length).toBe(6);
  });

  it('should have Door Pin as the first button', () => {
    expect(component.buttons[0].label).toBe('Door Pin');
    expect(component.buttons[0].icon).toBe('dialpad');
  });

  it('should have Settings as the second button', () => {
    expect(component.buttons[1].label).toBe('Settings');
    expect(component.buttons[1].icon).toBe('settings');
  });

  it('should open KeypadDialogComponent when Door Pin is clicked', () => {
    component.onButtonClick('Door Pin');
    expect(dialogSpy.open).toHaveBeenCalledWith(KeypadDialogComponent, {
      width: '260px',
      panelClass: 'dark-dialog',
    });
  });

  it('should open UpdateCodeDialogComponent when Settings is clicked', () => {
    component.onButtonClick('Settings');
    expect(dialogSpy.open).toHaveBeenCalledWith(UpdateCodeDialogComponent, {
      width: '360px',
      panelClass: 'dark-dialog',
    });
  });

  it('should not open any dialog for other buttons', () => {
    component.onButtonClick('Snapshot');
    expect(dialogSpy.open).not.toHaveBeenCalled();
  });
});
