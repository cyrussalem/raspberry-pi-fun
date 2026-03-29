import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { DashboardComponent } from './dashboard.component';
import { KeypadDialogComponent } from '../dialogs/keypad-dialog/keypad-dialog.component';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let dialogSpy: jest.SpyObj<MatDialog>;
  let routerSpy: jest.SpyObj<Router>;

  beforeEach(async () => {
    dialogSpy = { open: jest.fn() } as any;
    routerSpy = { navigate: jest.fn() } as any;

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
    })
      .overrideComponent(DashboardComponent, {
        set: {
          providers: [
            { provide: MatDialog, useValue: dialogSpy },
            { provide: Router, useValue: routerSpy },
          ],
        },
      })
      .compileComponents();

    const fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have a stream URL', () => {
    expect(component.streamUrl).toContain('/api/video/stream');
  });

  it('should have 6 buttons', () => {
    expect(component.buttons.length).toBe(6);
  });

  it('should open keypad dialog for Door Pin', () => {
    component.onButtonClick('Door Pin');
    expect(dialogSpy.open).toHaveBeenCalledWith(KeypadDialogComponent, {
      width: '520px',
      panelClass: 'dark-dialog',
    });
  });

  it('should navigate to settings for Settings button', () => {
    component.onButtonClick('Settings');
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/settings']);
  });

  it('should not navigate or open dialog for other buttons', () => {
    component.onButtonClick('Snapshot');
    expect(dialogSpy.open).not.toHaveBeenCalled();
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });
});
